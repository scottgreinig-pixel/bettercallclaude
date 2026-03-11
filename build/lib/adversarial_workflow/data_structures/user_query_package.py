"""UserQueryPackage data structure for adversarial workflow input.

This module implements the YAML-based schema for user legal queries with:
- Multi-jurisdictional support (federal + 6 cantons: ZH, BE, GE, BS, VD, TI)
- Multi-lingual detection (DE/FR/IT/EN with ≥95% confidence)
- Input validation (query minimum 20 characters)
- Metadata tracking (timestamp, session_id)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

import yaml

# Type aliases for clarity
JurisdictionLevel = Literal["federal", "cantonal"]
CantonCode = Literal["ZH", "BE", "GE", "BS", "VD", "TI"]
LanguageCode = Literal["de", "fr", "it", "en"]


@dataclass
class Jurisdiction:
    """Jurisdiction information for legal query.

    Attributes:
        level: Federal or cantonal jurisdiction
        canton_code: Required for cantonal jurisdiction (ZH/BE/GE/BS/VD/TI)
    """

    level: JurisdictionLevel
    canton_code: CantonCode | None = None

    def __post_init__(self) -> None:
        """Validate jurisdiction data after initialization."""
        # Validate level
        if self.level not in ("federal", "cantonal"):
            raise ValueError("level must be 'federal' or 'cantonal'")

        # Cantonal jurisdiction requires canton_code
        if self.level == "cantonal":
            if self.canton_code is None:
                raise ValueError("cantonal jurisdiction requires canton_code")

            # Validate canton_code against v1.0 supported cantons
            valid_cantons = ("ZH", "BE", "GE", "BS", "VD", "TI")
            if self.canton_code not in valid_cantons:
                raise ValueError(
                    f"canton_code must be one of {valid_cantons}, got '{self.canton_code}'"
                )

        # Federal jurisdiction should not have canton_code
        if self.level == "federal" and self.canton_code is not None:
            raise ValueError("federal jurisdiction should not specify canton_code")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {"level": self.level}
        if self.canton_code is not None:
            result["canton_code"] = self.canton_code
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Jurisdiction":
        """Create from dictionary."""
        return cls(level=data["level"], canton_code=data.get("canton_code"))


@dataclass
class Language:
    """Language detection information.

    Attributes:
        detected: Detected language code (de/fr/it/en)
        confidence: Detection confidence (≥0.95 for 95% accuracy target)
    """

    detected: LanguageCode
    confidence: float

    def __post_init__(self) -> None:
        """Validate language data after initialization."""
        # Validate detected language code
        valid_languages = ("de", "fr", "it", "en")
        if self.detected not in valid_languages:
            raise ValueError(
                f"detected language must be one of {valid_languages}, got '{self.detected}'"
            )

        # Validate confidence meets 95% accuracy target
        if self.confidence < 0.95:
            raise ValueError(
                f"confidence must be at least 0.95 (95% accuracy), got {self.confidence}"
            )

        # Confidence cannot exceed 100%
        if self.confidence > 1.0:
            raise ValueError(f"confidence must be between 0.95 and 1.0, got {self.confidence}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"detected": self.detected, "confidence": self.confidence}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Language":
        """Create from dictionary."""
        return cls(detected=data["detected"], confidence=data["confidence"])


@dataclass
class Metadata:
    """Metadata for query tracking.

    Attributes:
        timestamp: ISO 8601 timestamp (e.g., "2024-01-05T10:30:00Z")
        session_id: Unique session identifier (UUID format recommended)
    """

    timestamp: str
    session_id: str

    def __post_init__(self) -> None:
        """Validate metadata after initialization."""
        # Validate timestamp is ISO 8601 format
        try:
            datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(
                f"timestamp must be ISO 8601 format (e.g., '2024-01-05T10:30:00Z'), "
                f"got '{self.timestamp}'"
            ) from None

        # Validate session_id is non-empty
        if not self.session_id or not self.session_id.strip():
            raise ValueError("session_id cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"timestamp": self.timestamp, "session_id": self.session_id}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Metadata":
        """Create from dictionary."""
        return cls(timestamp=data["timestamp"], session_id=data["session_id"])


@dataclass
class UserQueryPackage:
    """Complete user query package with validation.

    This is the input schema for the adversarial workflow system. It captures:
    - The legal query text (minimum 20 characters)
    - Jurisdiction information (federal or cantonal with canton code)
    - Language detection (DE/FR/IT/EN with ≥95% confidence)
    - Session metadata (timestamp and session ID)

    Example YAML:
        query_text: "Vertragshaftung gemäss Art. 97 OR - analysis required"
        jurisdiction:
          level: federal
        language:
          detected: de
          confidence: 0.98
        metadata:
          timestamp: "2024-01-05T10:30:00Z"
          session_id: "550e8400-e29b-41d4-a716-446655440000"

    Attributes:
        query_text: Legal query (min 20 characters, no whitespace-only)
        jurisdiction: Federal or cantonal with optional canton code
        language: Detected language with confidence score
        metadata: Timestamp and session tracking
    """

    query_text: str
    jurisdiction: Jurisdiction
    language: Language
    metadata: Metadata

    def __post_init__(self) -> None:
        """Validate query package after initialization."""
        # Validate query_text is non-empty
        if not self.query_text:
            raise ValueError("query_text cannot be empty")

        # Validate query_text is not whitespace-only
        if not self.query_text.strip():
            raise ValueError("query_text cannot be whitespace only")

        # Validate query_text minimum length (20 characters)
        if len(self.query_text) < 20:
            raise ValueError(
                f"query_text must be at least 20 characters, got {len(self.query_text)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all UserQueryPackage fields
        """
        return {
            "query_text": self.query_text,
            "jurisdiction": self.jurisdiction.to_dict(),
            "language": self.language.to_dict(),
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserQueryPackage":
        """Create UserQueryPackage from dictionary.

        Args:
            data: Dictionary with query package fields

        Returns:
            UserQueryPackage instance

        Raises:
            ValueError: If required fields missing or validation fails
        """
        # Validate required fields
        required_fields = ["query_text", "jurisdiction", "language", "metadata"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"{field_name} is required")

        # Create nested objects
        jurisdiction = Jurisdiction.from_dict(data["jurisdiction"])
        language = Language.from_dict(data["language"])
        metadata = Metadata.from_dict(data["metadata"])

        return cls(
            query_text=data["query_text"],
            jurisdiction=jurisdiction,
            language=language,
            metadata=metadata,
        )

    def to_yaml(self) -> str:
        """Serialize to YAML format.

        Returns:
            YAML string representation
        """
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "UserQueryPackage":
        """Deserialize from YAML format.

        Args:
            yaml_str: YAML string representation

        Returns:
            UserQueryPackage instance

        Raises:
            ValueError: If YAML invalid or validation fails
        """
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}") from e

        return cls.from_dict(data)


# Export public API
__all__ = [
    "UserQueryPackage",
    "Jurisdiction",
    "Language",
    "Metadata",
    "JurisdictionLevel",
    "CantonCode",
    "LanguageCode",
]
