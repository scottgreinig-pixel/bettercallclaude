"""
Case Storage Backends for BetterCallClaude

Provides pluggable storage backends for case persistence.
Default implementation uses JSON files for simplicity.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CaseStorage(ABC):
    """
    Abstract base class for case storage backends.

    Implementations can use different storage mechanisms:
    - JSON files (default)
    - SQLite database
    - PostgreSQL
    - Cloud storage (S3, GCS)
    """

    @abstractmethod
    async def save_case(self, case_id: str, data: dict[str, Any]) -> bool:
        """
        Save case data to storage.

        Args:
            case_id: Unique case identifier
            data: Case data dictionary

        Returns:
            True if save successful
        """
        pass

    @abstractmethod
    async def load_case(self, case_id: str) -> dict[str, Any] | None:
        """
        Load case data from storage.

        Args:
            case_id: Unique case identifier

        Returns:
            Case data dictionary or None if not found
        """
        pass

    @abstractmethod
    async def delete_case(self, case_id: str) -> bool:
        """
        Delete case from storage.

        Args:
            case_id: Unique case identifier

        Returns:
            True if deletion successful
        """
        pass

    @abstractmethod
    async def list_cases(
        self,
        firm_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List cases with optional filtering.

        Args:
            firm_id: Filter by firm
            status: Filter by status (active, archived, closed)
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of case metadata dictionaries
        """
        pass

    @abstractmethod
    async def case_exists(self, case_id: str) -> bool:
        """Check if a case exists in storage."""
        pass


class JSONFileCaseStorage(CaseStorage):
    """
    JSON file-based case storage.

    Stores each case as a separate JSON file in a configured directory.
    Includes an index file for efficient listing and searching.

    Directory structure:
        cases/
        ├── index.json          # Case index for fast listing
        ├── MUL-2025-001.json   # Individual case files
        ├── ABC-2025-002.json
        └── ...
    """

    def __init__(self, storage_dir: str = ".bettercallclaude/cases"):
        """
        Initialize JSON file storage.

        Args:
            storage_dir: Directory for case files (relative to cwd or absolute)
        """
        self.storage_dir = Path(storage_dir).expanduser()
        self.index_file = self.storage_dir / "index.json"
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Create empty index if it doesn't exist
        if not self.index_file.exists():
            self._save_index({})

    def _get_case_file(self, case_id: str) -> Path:
        """Get file path for a case."""
        # Sanitize case_id for filename
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in case_id)
        return self.storage_dir / f"{safe_id}.json"

    def _load_index(self) -> dict[str, dict[str, Any]]:
        """Load the case index."""
        try:
            if self.index_file.exists():
                with open(self.index_file, encoding="utf-8") as f:
                    result: dict[str, dict[str, Any]] = json.load(f)
                    return result
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load case index: {e}")
        return {}

    def _save_index(self, index: dict[str, dict[str, Any]]) -> None:
        """Save the case index."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Failed to save case index: {e}")

    async def save_case(self, case_id: str, data: dict[str, Any]) -> bool:
        """Save case data to JSON file."""
        try:
            case_file = self._get_case_file(case_id)

            # Save full case data
            with open(case_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            # Update index with metadata
            index = self._load_index()
            index[case_id] = {
                "case_id": case_id,
                "title": data.get("title", ""),
                "case_type": data.get("case_type", "other"),
                "status": data.get("status", "active"),
                "firm_id": data.get("firm_id", "default"),
                "created_at": data.get("created_at", datetime.utcnow().isoformat()),
                "updated_at": datetime.utcnow().isoformat(),
                "file_path": str(case_file),
            }
            self._save_index(index)

            logger.info(f"Saved case {case_id} to {case_file}")
            return True

        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Failed to save case {case_id}: {e}")
            return False

    async def load_case(self, case_id: str) -> dict[str, Any] | None:
        """Load case data from JSON file."""
        try:
            case_file = self._get_case_file(case_id)

            if not case_file.exists():
                logger.warning(f"Case file not found: {case_file}")
                return None

            with open(case_file, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)

            logger.info(f"Loaded case {case_id} from {case_file}")
            return data

        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load case {case_id}: {e}")
            return None

    async def delete_case(self, case_id: str) -> bool:
        """Delete case from storage."""
        try:
            case_file = self._get_case_file(case_id)

            if case_file.exists():
                os.remove(case_file)

            # Remove from index
            index = self._load_index()
            if case_id in index:
                del index[case_id]
                self._save_index(index)

            logger.info(f"Deleted case {case_id}")
            return True

        except OSError as e:
            logger.error(f"Failed to delete case {case_id}: {e}")
            return False

    async def list_cases(
        self,
        firm_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List cases with optional filtering."""
        index = self._load_index()
        cases = list(index.values())

        # Apply filters
        if firm_id:
            cases = [c for c in cases if c.get("firm_id") == firm_id]
        if status:
            cases = [c for c in cases if c.get("status") == status]

        # Sort by updated_at descending
        cases.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        # Apply pagination
        return cases[offset : offset + limit]

    async def case_exists(self, case_id: str) -> bool:
        """Check if a case exists."""
        case_file = self._get_case_file(case_id)
        return case_file.exists()

    async def search_cases(
        self, query: str, firm_id: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search cases by title.

        Args:
            query: Search query (matched against title)
            firm_id: Optional firm filter
            limit: Maximum results

        Returns:
            List of matching case metadata
        """
        index = self._load_index()
        query_lower = query.lower()

        results = []
        for case_data in index.values():
            if firm_id and case_data.get("firm_id") != firm_id:
                continue

            title = case_data.get("title", "").lower()
            case_id = case_data.get("case_id", "").lower()

            if query_lower in title or query_lower in case_id:
                results.append(case_data)

        # Sort by relevance (title match first)
        results.sort(
            key=lambda x: (
                query_lower in x.get("case_id", "").lower(),
                query_lower in x.get("title", "").lower(),
            ),
            reverse=True,
        )

        return results[:limit]
