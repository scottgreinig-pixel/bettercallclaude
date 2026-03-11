"""
CaseManager for BetterCallClaude

Central manager for case context operations including:
- Case creation with validation
- Case loading and persistence
- Case lifecycle management (open, close, archive)
- Export functionality
- Summary generation
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .storage import CaseStorage, JSONFileCaseStorage

logger = logging.getLogger(__name__)


class CaseStatus(Enum):
    """Case lifecycle status."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    CLOSED = "closed"


class CaseType(Enum):
    """Type of legal case."""

    LITIGATION = "litigation"
    CORPORATE = "corporate"
    CONTRACT = "contract"
    REGULATORY = "regulatory"
    OTHER = "other"


@dataclass
class Party:
    """Represents a party in a legal case."""

    name: str
    role: str  # client, plaintiff, defendant, opposing, related
    contact: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "contact": self.contact,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Party":
        return cls(
            name=data.get("name", ""),
            role=data.get("role", "related"),
            contact=data.get("contact"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Deadline:
    """A procedural deadline in a case."""

    name: str
    due_date: datetime
    description: str = ""
    completed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "due_date": self.due_date.isoformat(),
            "description": self.description,
            "completed": self.completed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Deadline":
        due_date = data.get("due_date", "")
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        return cls(
            name=data.get("name", ""),
            due_date=due_date,
            description=data.get("description", ""),
            completed=data.get("completed", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Milestone:
    """A milestone in a case."""

    name: str
    date: datetime
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "date": self.date.isoformat(),
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Milestone":
        date = data.get("date", "")
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        return cls(
            name=data.get("name", ""),
            date=date,
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LegalIssue:
    """A legal issue identified in a case."""

    description: str
    legal_area: str  # e.g., OR, ZGB, StGB
    relevant_articles: list[str] = field(default_factory=list)
    status: str = "open"  # open, resolved, superseded
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "legal_area": self.legal_area,
            "relevant_articles": self.relevant_articles,
            "status": self.status,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LegalIssue":
        return cls(
            description=data.get("description", ""),
            legal_area=data.get("legal_area", ""),
            relevant_articles=data.get("relevant_articles", []),
            status=data.get("status", "open"),
            notes=data.get("notes", ""),
        )


@dataclass
class AgentExecution:
    """Record of an agent execution on a case."""

    agent_id: str
    timestamp: datetime
    task: str
    outcome: str  # success, partial, failed
    summary: str = ""
    audit_log_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "task": self.task,
            "outcome": self.outcome,
            "summary": self.summary,
            "audit_log_id": self.audit_log_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentExecution":
        timestamp = data.get("timestamp", "")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            agent_id=data.get("agent_id", ""),
            timestamp=timestamp,
            task=data.get("task", ""),
            outcome=data.get("outcome", "unknown"),
            summary=data.get("summary", ""),
            audit_log_id=data.get("audit_log_id"),
        )


@dataclass
class Finding:
    """A finding or insight from agent work."""

    content: str
    source: str  # agent_id or "manual"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    category: str = "general"  # general, precedent, risk, opportunity
    confidence: float = 1.0
    citations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category,
            "confidence": self.confidence,
            "citations": self.citations,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Finding":
        timestamp = data.get("timestamp", "")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            content=data.get("content", ""),
            source=data.get("source", "unknown"),
            timestamp=timestamp,
            category=data.get("category", "general"),
            confidence=data.get("confidence", 1.0),
            citations=data.get("citations", []),
        )


@dataclass
class DocumentRef:
    """Reference to a document in a case."""

    name: str
    path: str
    document_type: str  # brief, contract, correspondence, evidence, research
    added_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "document_type": self.document_type,
            "added_at": self.added_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentRef":
        added_at = data.get("added_at", "")
        if isinstance(added_at, str):
            added_at = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
        return cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            document_type=data.get("document_type", "other"),
            added_at=added_at,
            metadata=data.get("metadata", {}),
        )


@dataclass
class ManagedCaseContext:
    """
    Complete case context with full lifecycle management.

    This extends the base CaseContext with additional fields for
    case management operations.
    """

    # Identity
    case_id: str
    title: str
    case_type: CaseType = CaseType.OTHER
    status: CaseStatus = CaseStatus.ACTIVE

    # Firm and User
    firm_id: str = "default"
    created_by: str = "anonymous"

    # Jurisdiction
    jurisdiction_federal: bool = True
    jurisdiction_cantons: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=lambda: ["DE"])

    # Parties
    parties: list[Party] = field(default_factory=list)

    # Timeline
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    deadlines: list[Deadline] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)

    # Facts and Issues
    facts: list[str] = field(default_factory=list)
    legal_issues: list[LegalIssue] = field(default_factory=list)

    # Agent Work
    agent_history: list[AgentExecution] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    documents: list[DocumentRef] = field(default_factory=list)

    # Metadata
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize case context to dictionary for storage."""
        return {
            "case_id": self.case_id,
            "title": self.title,
            "case_type": (
                self.case_type.value if isinstance(self.case_type, CaseType) else self.case_type
            ),
            "status": self.status.value if isinstance(self.status, CaseStatus) else self.status,
            "firm_id": self.firm_id,
            "created_by": self.created_by,
            "jurisdiction": {
                "federal": self.jurisdiction_federal,
                "cantons": self.jurisdiction_cantons,
                "languages": self.languages,
            },
            "parties": [p.to_dict() for p in self.parties],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "deadlines": [d.to_dict() for d in self.deadlines],
            "milestones": [m.to_dict() for m in self.milestones],
            "facts": self.facts,
            "legal_issues": [i.to_dict() for i in self.legal_issues],
            "agent_history": [a.to_dict() for a in self.agent_history],
            "findings": [f.to_dict() for f in self.findings],
            "documents": [d.to_dict() for d in self.documents],
            "tags": self.tags,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManagedCaseContext":
        """Deserialize case context from dictionary."""
        jurisdiction = data.get("jurisdiction", {})

        # Parse datetime fields
        def parse_dt(value: Any) -> datetime | None:
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return None

        return cls(
            case_id=data.get("case_id", ""),
            title=data.get("title", ""),
            case_type=CaseType(data.get("case_type", "other")),
            status=CaseStatus(data.get("status", "active")),
            firm_id=data.get("firm_id", "default"),
            created_by=data.get("created_by", "anonymous"),
            jurisdiction_federal=jurisdiction.get("federal", True),
            jurisdiction_cantons=jurisdiction.get("cantons", []),
            languages=jurisdiction.get("languages", ["DE"]),
            parties=[Party.from_dict(p) for p in data.get("parties", [])],
            created_at=parse_dt(data.get("created_at")) or datetime.utcnow(),
            updated_at=parse_dt(data.get("updated_at")) or datetime.utcnow(),
            opened_at=parse_dt(data.get("opened_at")),
            closed_at=parse_dt(data.get("closed_at")),
            deadlines=[Deadline.from_dict(d) for d in data.get("deadlines", [])],
            milestones=[Milestone.from_dict(m) for m in data.get("milestones", [])],
            facts=data.get("facts", []),
            legal_issues=[LegalIssue.from_dict(i) for i in data.get("legal_issues", [])],
            agent_history=[AgentExecution.from_dict(a) for a in data.get("agent_history", [])],
            findings=[Finding.from_dict(f) for f in data.get("findings", [])],
            documents=[DocumentRef.from_dict(d) for d in data.get("documents", [])],
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", {}),
        )

    def to_agent_context(self) -> dict[str, Any]:
        """
        Convert to lightweight context for agent consumption.

        Returns a simplified version suitable for passing to agents.
        """
        return {
            "case_id": self.case_id,
            "title": self.title,
            "case_type": (
                self.case_type.value if isinstance(self.case_type, CaseType) else self.case_type
            ),
            "jurisdiction_federal": self.jurisdiction_federal,
            "jurisdiction_cantons": self.jurisdiction_cantons,
            "languages": self.languages,
            "parties": [p.to_dict() for p in self.parties],
            "facts": self.facts,
            "legal_issues": [i.description for i in self.legal_issues],
            "agent_history": [a.agent_id for a in self.agent_history[-10:]],  # Last 10
            "findings": self.findings,
            "created_at": self.created_at,
        }


class CaseManager:
    """
    Central manager for case context operations.

    Provides high-level operations for case management:
    - Creating new cases with validation
    - Loading and saving cases
    - Case lifecycle (open, close, archive)
    - Export functionality
    - Summary generation

    Example:
        manager = CaseManager()

        # Create a new case
        case = await manager.create_case(
            title="Müller vs. ABC AG",
            case_type=CaseType.LITIGATION,
            jurisdiction_cantons=["ZH"],
            parties=[Party(name="Hans Müller", role="client")]
        )

        # Load existing case
        case = await manager.open_case("MUL-2025-001")

        # Add findings from agent work
        await manager.add_finding(
            case.case_id,
            Finding(
                content="Relevant BGE 147 IV 73 on contract interpretation",
                source="researcher",
                category="precedent"
            )
        )

        # Close case
        await manager.close_case(case.case_id)
    """

    def __init__(
        self,
        storage: CaseStorage | None = None,
        default_firm_id: str = "default",
    ):
        """
        Initialize CaseManager.

        Args:
            storage: Case storage backend (defaults to JSON file storage)
            default_firm_id: Default firm ID for new cases
        """
        self.storage = storage or JSONFileCaseStorage()
        self.default_firm_id = default_firm_id
        self._current_case: ManagedCaseContext | None = None

    @property
    def current_case(self) -> ManagedCaseContext | None:
        """Get the currently active case context."""
        return self._current_case

    def _generate_case_id(self, title: str) -> str:
        """
        Generate a unique case ID from title.

        Format: [PREFIX]-[YEAR]-[NUMBER]
        Example: MUL-2025-001
        """
        # Extract prefix from title (first 3 letters of first word)
        words = title.split()
        prefix = words[0][:3].upper() if words else "CAS"

        # Add year and unique suffix
        year = datetime.utcnow().year
        unique_suffix = str(uuid.uuid4())[:4].upper()

        return f"{prefix}-{year}-{unique_suffix}"

    async def create_case(
        self,
        title: str,
        case_type: CaseType = CaseType.OTHER,
        jurisdiction_federal: bool = True,
        jurisdiction_cantons: list[str] | None = None,
        languages: list[str] | None = None,
        parties: list[Party] | None = None,
        facts: list[str] | None = None,
        legal_issues: list[LegalIssue] | None = None,
        user_id: str = "anonymous",
        firm_id: str | None = None,
        tags: list[str] | None = None,
        notes: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ManagedCaseContext:
        """
        Create a new case with the provided details.

        Args:
            title: Case title (e.g., "Müller vs. ABC AG")
            case_type: Type of case
            jurisdiction_federal: Whether federal jurisdiction applies
            jurisdiction_cantons: List of relevant cantons
            languages: Working languages
            parties: List of parties involved
            facts: Initial case facts
            legal_issues: Initial legal issues
            user_id: Creating user
            firm_id: Firm identifier
            tags: Optional tags for categorization
            notes: Initial notes
            metadata: Additional metadata

        Returns:
            Created ManagedCaseContext
        """
        case_id = self._generate_case_id(title)

        case = ManagedCaseContext(
            case_id=case_id,
            title=title,
            case_type=case_type,
            status=CaseStatus.ACTIVE,
            firm_id=firm_id or self.default_firm_id,
            created_by=user_id,
            jurisdiction_federal=jurisdiction_federal,
            jurisdiction_cantons=jurisdiction_cantons or [],
            languages=languages or ["DE"],
            parties=parties or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            opened_at=datetime.utcnow(),
            facts=facts or [],
            legal_issues=legal_issues or [],
            tags=tags or [],
            notes=notes,
            metadata=metadata or {},
        )

        # Persist the case
        await self.storage.save_case(case_id, case.to_dict())

        # Set as current case
        self._current_case = case

        logger.info(f"Created case: {case_id} - {title}")
        return case

    async def open_case(self, case_id: str) -> ManagedCaseContext | None:
        """
        Load and open an existing case.

        Args:
            case_id: Case identifier

        Returns:
            ManagedCaseContext or None if not found
        """
        data = await self.storage.load_case(case_id)

        if data is None:
            logger.warning(f"Case not found: {case_id}")
            return None

        case = ManagedCaseContext.from_dict(data)
        self._current_case = case

        logger.info(f"Opened case: {case_id}")
        return case

    async def save_case(self, case: ManagedCaseContext | None = None) -> bool:
        """
        Save the case to storage.

        Args:
            case: Case to save (defaults to current case)

        Returns:
            True if save successful
        """
        case = case or self._current_case

        if case is None:
            logger.warning("No case to save")
            return False

        case.updated_at = datetime.utcnow()
        return await self.storage.save_case(case.case_id, case.to_dict())

    async def close_case(self, case_id: str | None = None, reason: str = "") -> bool:
        """
        Close a case (archive with closure date).

        Args:
            case_id: Case to close (defaults to current case)
            reason: Reason for closure

        Returns:
            True if closure successful
        """
        if case_id is None and self._current_case:
            case_id = self._current_case.case_id

        if case_id is None:
            logger.warning("No case specified for closure")
            return False

        # Load case if not current
        case: ManagedCaseContext | None
        if self._current_case and self._current_case.case_id == case_id:
            case = self._current_case
        else:
            case = await self.open_case(case_id)

        if case is None:
            return False

        case.status = CaseStatus.CLOSED
        case.closed_at = datetime.utcnow()
        if reason:
            case.notes += f"\n\nClosure reason ({datetime.utcnow().isoformat()}): {reason}"

        success = await self.save_case(case)

        if success and self._current_case and self._current_case.case_id == case_id:
            self._current_case = None

        logger.info(f"Closed case: {case_id}")
        return success

    async def archive_case(self, case_id: str | None = None) -> bool:
        """
        Archive a case (mark as archived but keep accessible).

        Args:
            case_id: Case to archive (defaults to current case)

        Returns:
            True if archival successful
        """
        if case_id is None and self._current_case:
            case_id = self._current_case.case_id

        if case_id is None:
            return False

        case = await self.open_case(case_id)
        if case is None:
            return False

        case.status = CaseStatus.ARCHIVED
        success = await self.save_case(case)

        logger.info(f"Archived case: {case_id}")
        return success

    async def list_cases(
        self,
        firm_id: str | None = None,
        status: CaseStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List cases with optional filtering.

        Args:
            firm_id: Filter by firm
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of case metadata
        """
        status_str = status.value if status else None
        return await self.storage.list_cases(
            firm_id=firm_id,
            status=status_str,
            limit=limit,
            offset=offset,
        )

    async def generate_summary(self, case_id: str | None = None) -> dict[str, Any]:
        """
        Generate a case status overview.

        Args:
            case_id: Case to summarize (defaults to current case)

        Returns:
            Summary dictionary
        """
        case: ManagedCaseContext | None
        if case_id is None and self._current_case:
            case = self._current_case
        else:
            case = await self.open_case(case_id or "")

        if case is None:
            return {"error": "Case not found"}

        # Calculate statistics
        pending_deadlines = [d for d in case.deadlines if not d.completed]
        overdue_deadlines = [d for d in pending_deadlines if d.due_date < datetime.utcnow()]

        return {
            "case_id": case.case_id,
            "title": case.title,
            "case_type": (
                case.case_type.value if isinstance(case.case_type, CaseType) else case.case_type
            ),
            "status": case.status.value if isinstance(case.status, CaseStatus) else case.status,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "parties_count": len(case.parties),
            "facts_count": len(case.facts),
            "legal_issues": [
                {"description": i.description, "status": i.status} for i in case.legal_issues
            ],
            "deadlines": {
                "total": len(case.deadlines),
                "pending": len(pending_deadlines),
                "overdue": len(overdue_deadlines),
                "next": pending_deadlines[0].to_dict() if pending_deadlines else None,
            },
            "agent_executions": len(case.agent_history),
            "findings_count": len(case.findings),
            "documents_count": len(case.documents),
            "last_updated": case.updated_at.isoformat() if case.updated_at else None,
        }

    async def export_case(
        self,
        case_id: str | None = None,
        format: str = "json",
        include_audit: bool = False,
    ) -> str:
        """
        Export case data for external use.

        Args:
            case_id: Case to export (defaults to current case)
            format: Export format (json, markdown)
            include_audit: Whether to include full audit trail

        Returns:
            Exported case data as string
        """
        case: ManagedCaseContext | None
        if case_id is None and self._current_case:
            case = self._current_case
        else:
            case = await self.open_case(case_id or "")

        if case is None:
            return '{"error": "Case not found"}'

        if format == "json":
            return json.dumps(case.to_dict(), indent=2, ensure_ascii=False, default=str)

        elif format == "markdown":
            lines = [
                f"# Case: {case.title}",
                "",
                f"**Case ID**: {case.case_id}",
                f"**Type**: {case.case_type.value if isinstance(case.case_type, CaseType) else case.case_type}",  # noqa: E501
                f"**Status**: {case.status.value if isinstance(case.status, CaseStatus) else case.status}",  # noqa: E501
                f"**Created**: {case.created_at.isoformat() if case.created_at else 'N/A'}",
                "",
                "## Jurisdiction",
                f"- Federal: {'Yes' if case.jurisdiction_federal else 'No'}",
                f"- Cantons: {', '.join(case.jurisdiction_cantons) or 'None specified'}",
                f"- Languages: {', '.join(case.languages)}",
                "",
                "## Parties",
            ]

            for party in case.parties:
                lines.append(f"- **{party.role.capitalize()}**: {party.name}")

            lines.extend(["", "## Facts"])
            for i, fact in enumerate(case.facts, 1):
                lines.append(f"{i}. {fact}")

            if case.legal_issues:
                lines.extend(["", "## Legal Issues"])
                for issue in case.legal_issues:
                    lines.append(f"- [{issue.status}] {issue.description}")
                    if issue.relevant_articles:
                        lines.append(f"  - Articles: {', '.join(issue.relevant_articles)}")

            if case.findings:
                lines.extend(["", "## Key Findings"])
                for finding in case.findings[-10:]:  # Last 10 findings
                    lines.append(f"- **{finding.category}** ({finding.source}): {finding.content}")

            if case.deadlines:
                lines.extend(["", "## Deadlines"])
                for deadline in sorted(case.deadlines, key=lambda d: d.due_date):
                    status = (
                        "✅"
                        if deadline.completed
                        else ("⚠️" if deadline.due_date < datetime.utcnow() else "⏳")
                    )
                    lines.append(
                        f"- {status} **{deadline.name}**: {deadline.due_date.strftime('%Y-%m-%d')}"
                    )

            if case.notes:
                lines.extend(["", "## Notes", case.notes])

            return "\n".join(lines)

        else:
            return f'{{"error": "Unsupported format: {format}"}}'

    # -------------------------------------------------------------------------
    # Case Content Modification Methods
    # -------------------------------------------------------------------------

    async def add_party(self, case_id: str | None, party: Party) -> bool:
        """Add a party to a case."""
        case = await self._get_case(case_id)
        if case is None:
            return False

        case.parties.append(party)
        return await self.save_case(case)

    async def add_fact(self, case_id: str | None, fact: str) -> bool:
        """Add a fact to a case."""
        case = await self._get_case(case_id)
        if case is None:
            return False

        case.facts.append(fact)
        return await self.save_case(case)

    async def add_legal_issue(self, case_id: str | None, issue: LegalIssue) -> bool:
        """Add a legal issue to a case."""
        case = await self._get_case(case_id)
        if case is None:
            return False

        case.legal_issues.append(issue)
        return await self.save_case(case)

    async def add_deadline(self, case_id: str | None, deadline: Deadline) -> bool:
        """Add a deadline to a case."""
        case = await self._get_case(case_id)
        if case is None:
            return False

        case.deadlines.append(deadline)
        return await self.save_case(case)

    async def add_finding(self, case_id: str | None, finding: Finding) -> bool:
        """Add a finding from agent work."""
        case = await self._get_case(case_id)
        if case is None:
            return False

        case.findings.append(finding)
        return await self.save_case(case)

    async def add_document(self, case_id: str | None, document: DocumentRef) -> bool:
        """Add a document reference to a case."""
        case = await self._get_case(case_id)
        if case is None:
            return False

        case.documents.append(document)
        return await self.save_case(case)

    async def record_agent_execution(self, case_id: str | None, execution: AgentExecution) -> bool:
        """Record an agent execution on a case."""
        case = await self._get_case(case_id)
        if case is None:
            return False

        case.agent_history.append(execution)
        return await self.save_case(case)

    async def _get_case(self, case_id: str | None) -> ManagedCaseContext | None:
        """Get case by ID or return current case."""
        if case_id is None and self._current_case:
            return self._current_case
        if case_id:
            return await self.open_case(case_id)
        return None
