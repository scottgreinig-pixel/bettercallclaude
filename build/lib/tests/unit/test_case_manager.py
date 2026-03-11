"""
Unit tests for CaseManager

Tests the CaseManager and related data classes from src/core/case/manager.py
"""

import json
from datetime import datetime, timedelta
from typing import Any

import pytest

from src.core.case.manager import (
    AgentExecution,
    CaseManager,
    CaseStatus,
    CaseType,
    Deadline,
    DocumentRef,
    Finding,
    LegalIssue,
    ManagedCaseContext,
    Milestone,
    Party,
)
from src.core.case.storage import CaseStorage

# =============================================================================
# Test Fixtures
# =============================================================================


class MockCaseStorage(CaseStorage):
    """In-memory mock storage for testing."""

    def __init__(self) -> None:
        self._cases: dict[str, dict[str, Any]] = {}

    async def save_case(self, case_id: str, data: dict[str, Any]) -> bool:
        self._cases[case_id] = data
        return True

    async def load_case(self, case_id: str) -> dict[str, Any] | None:
        return self._cases.get(case_id)

    async def delete_case(self, case_id: str) -> bool:
        if case_id in self._cases:
            del self._cases[case_id]
            return True
        return False

    async def list_cases(
        self,
        firm_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        results = []
        for case_id, data in self._cases.items():
            if firm_id and data.get("firm_id") != firm_id:
                continue
            if status and data.get("status") != status:
                continue
            results.append(
                {
                    "case_id": case_id,
                    "title": data.get("title", ""),
                    "status": data.get("status", "active"),
                    "case_type": data.get("case_type", "other"),
                }
            )
        return results[offset : offset + limit]

    async def case_exists(self, case_id: str) -> bool:
        """Check if a case exists in storage."""
        return case_id in self._cases


@pytest.fixture
def mock_storage() -> MockCaseStorage:
    """Provide a fresh mock storage for each test."""
    return MockCaseStorage()


@pytest.fixture
def case_manager(mock_storage: MockCaseStorage) -> CaseManager:
    """Provide a CaseManager with mock storage."""
    return CaseManager(storage=mock_storage)


# =============================================================================
# Enum Tests
# =============================================================================


class TestCaseStatus:
    """Test CaseStatus enum."""

    def test_enum_values(self) -> None:
        """Test case status enum has correct values."""
        assert CaseStatus.ACTIVE.value == "active"
        assert CaseStatus.ARCHIVED.value == "archived"
        assert CaseStatus.CLOSED.value == "closed"

    def test_enum_from_string(self) -> None:
        """Test creating enum from string value."""
        assert CaseStatus("active") == CaseStatus.ACTIVE
        assert CaseStatus("archived") == CaseStatus.ARCHIVED
        assert CaseStatus("closed") == CaseStatus.CLOSED


class TestCaseType:
    """Test CaseType enum."""

    def test_enum_values(self) -> None:
        """Test case type enum has correct values."""
        assert CaseType.LITIGATION.value == "litigation"
        assert CaseType.CORPORATE.value == "corporate"
        assert CaseType.CONTRACT.value == "contract"
        assert CaseType.REGULATORY.value == "regulatory"
        assert CaseType.OTHER.value == "other"


# =============================================================================
# Data Class Tests
# =============================================================================


class TestParty:
    """Test Party data class."""

    def test_create_party_minimal(self) -> None:
        """Test creating a party with minimal fields."""
        party = Party(name="Hans Müller", role="client")

        assert party.name == "Hans Müller"
        assert party.role == "client"
        assert party.contact is None
        assert party.metadata == {}

    def test_create_party_full(self) -> None:
        """Test creating a party with all fields."""
        party = Party(
            name="ABC AG",
            role="defendant",
            contact="legal@abc.ch",
            metadata={"address": "Zürich", "phone": "+41 44 123 45 67"},
        )

        assert party.name == "ABC AG"
        assert party.role == "defendant"
        assert party.contact == "legal@abc.ch"
        assert party.metadata["address"] == "Zürich"

    def test_party_to_dict(self) -> None:
        """Test party serialization."""
        party = Party(name="Test", role="witness", contact="test@test.ch")

        data = party.to_dict()

        assert data["name"] == "Test"
        assert data["role"] == "witness"
        assert data["contact"] == "test@test.ch"
        assert "metadata" in data

    def test_party_from_dict(self) -> None:
        """Test party deserialization."""
        data = {
            "name": "Restored Party",
            "role": "expert",
            "contact": None,
            "metadata": {"expertise": "finance"},
        }

        party = Party.from_dict(data)

        assert party.name == "Restored Party"
        assert party.role == "expert"
        assert party.metadata["expertise"] == "finance"


class TestDeadline:
    """Test Deadline data class."""

    def test_create_deadline(self) -> None:
        """Test creating a deadline."""
        due_date = datetime.utcnow() + timedelta(days=30)
        deadline = Deadline(
            name="Response to complaint",
            due_date=due_date,
            description="File response to plaintiff's complaint",
        )

        assert deadline.name == "Response to complaint"
        assert deadline.due_date == due_date
        assert deadline.completed is False

    def test_deadline_to_dict(self) -> None:
        """Test deadline serialization."""
        due_date = datetime(2025, 6, 15, 12, 0, 0)
        deadline = Deadline(name="Test", due_date=due_date, completed=True)

        data = deadline.to_dict()

        assert data["name"] == "Test"
        assert data["due_date"] == "2025-06-15T12:00:00"
        assert data["completed"] is True

    def test_deadline_from_dict(self) -> None:
        """Test deadline deserialization."""
        data = {
            "name": "Restored Deadline",
            "due_date": "2025-07-01T09:00:00",
            "description": "Test deadline",
            "completed": False,
        }

        deadline = Deadline.from_dict(data)

        assert deadline.name == "Restored Deadline"
        assert deadline.due_date.year == 2025
        assert deadline.due_date.month == 7


class TestMilestone:
    """Test Milestone data class."""

    def test_create_milestone(self) -> None:
        """Test creating a milestone."""
        date = datetime.utcnow()
        milestone = Milestone(
            name="Contract signed",
            date=date,
            description="Both parties signed the agreement",
        )

        assert milestone.name == "Contract signed"
        assert milestone.date == date

    def test_milestone_round_trip(self) -> None:
        """Test milestone serialization and deserialization."""
        original = Milestone(
            name="Court hearing",
            date=datetime(2025, 8, 15, 14, 30, 0),
            description="Initial hearing",
        )

        data = original.to_dict()
        restored = Milestone.from_dict(data)

        assert restored.name == original.name
        assert restored.date.year == original.date.year
        assert restored.description == original.description


class TestLegalIssue:
    """Test LegalIssue data class."""

    def test_create_legal_issue(self) -> None:
        """Test creating a legal issue."""
        issue = LegalIssue(
            description="Contract validity under Swiss law",
            legal_area="OR",
            relevant_articles=["Art. 1 OR", "Art. 18 OR"],
            status="open",
        )

        assert issue.description == "Contract validity under Swiss law"
        assert issue.legal_area == "OR"
        assert "Art. 1 OR" in issue.relevant_articles
        assert issue.status == "open"

    def test_legal_issue_round_trip(self) -> None:
        """Test legal issue serialization and deserialization."""
        original = LegalIssue(
            description="Tort liability",
            legal_area="OR",
            relevant_articles=["Art. 41 OR"],
            status="resolved",
            notes="Settled out of court",
        )

        data = original.to_dict()
        restored = LegalIssue.from_dict(data)

        assert restored.description == original.description
        assert restored.legal_area == original.legal_area
        assert restored.status == original.status
        assert restored.notes == original.notes


class TestAgentExecution:
    """Test AgentExecution data class."""

    def test_create_agent_execution(self) -> None:
        """Test creating an agent execution record."""
        execution = AgentExecution(
            agent_id="researcher",
            timestamp=datetime.utcnow(),
            task="Find relevant precedents for contract dispute",
            outcome="success",
            summary="Found 5 relevant BGE decisions",
            audit_log_id="log-123",
        )

        assert execution.agent_id == "researcher"
        assert execution.outcome == "success"
        assert "5 relevant" in execution.summary

    def test_agent_execution_round_trip(self) -> None:
        """Test agent execution serialization and deserialization."""
        timestamp = datetime(2025, 5, 20, 10, 30, 0)
        original = AgentExecution(
            agent_id="citation-checker",
            timestamp=timestamp,
            task="Verify citations",
            outcome="partial",
            summary="3 of 5 citations verified",
        )

        data = original.to_dict()
        restored = AgentExecution.from_dict(data)

        assert restored.agent_id == original.agent_id
        assert restored.outcome == original.outcome


class TestFinding:
    """Test Finding data class."""

    def test_create_finding(self) -> None:
        """Test creating a finding."""
        finding = Finding(
            content="BGE 147 IV 73 establishes relevant precedent",
            source="researcher",
            category="precedent",
            confidence=0.85,
            citations=["BGE 147 IV 73"],
        )

        assert "BGE 147 IV 73" in finding.content
        assert finding.source == "researcher"
        assert finding.category == "precedent"
        assert finding.confidence == 0.85

    def test_finding_round_trip(self) -> None:
        """Test finding serialization and deserialization."""
        original = Finding(
            content="Risk identified in contract clause 4.2",
            source="risk-assessor",
            category="risk",
            confidence=0.92,
        )

        data = original.to_dict()
        restored = Finding.from_dict(data)

        assert restored.content == original.content
        assert restored.source == original.source
        assert restored.confidence == original.confidence


class TestDocumentRef:
    """Test DocumentRef data class."""

    def test_create_document_ref(self) -> None:
        """Test creating a document reference."""
        doc = DocumentRef(
            name="Contract Agreement",
            path="/cases/TEST-001/documents/contract.pdf",
            document_type="contract",
            metadata={"pages": 25, "signed": True},
        )

        assert doc.name == "Contract Agreement"
        assert doc.document_type == "contract"
        assert doc.metadata["pages"] == 25

    def test_document_ref_round_trip(self) -> None:
        """Test document reference serialization and deserialization."""
        original = DocumentRef(
            name="Legal Brief",
            path="/cases/TEST-001/briefs/brief.docx",
            document_type="brief",
        )

        data = original.to_dict()
        restored = DocumentRef.from_dict(data)

        assert restored.name == original.name
        assert restored.path == original.path
        assert restored.document_type == original.document_type


# =============================================================================
# ManagedCaseContext Tests
# =============================================================================


class TestManagedCaseContext:
    """Test ManagedCaseContext data class."""

    def test_create_minimal_context(self) -> None:
        """Test creating a context with minimal fields."""
        context = ManagedCaseContext(
            case_id="TEST-2025-001",
            title="Test Case",
        )

        assert context.case_id == "TEST-2025-001"
        assert context.title == "Test Case"
        assert context.case_type == CaseType.OTHER
        assert context.status == CaseStatus.ACTIVE
        assert context.jurisdiction_federal is True
        assert context.parties == []
        assert context.facts == []

    def test_create_full_context(self) -> None:
        """Test creating a context with all fields."""
        party = Party(name="Client", role="client")
        deadline = Deadline(
            name="Filing deadline",
            due_date=datetime.utcnow() + timedelta(days=14),
        )
        issue = LegalIssue(
            description="Contract interpretation",
            legal_area="OR",
        )

        context = ManagedCaseContext(
            case_id="FULL-2025-001",
            title="Complete Test Case",
            case_type=CaseType.LITIGATION,
            status=CaseStatus.ACTIVE,
            firm_id="test-firm",
            created_by="test-user",
            jurisdiction_federal=False,
            jurisdiction_cantons=["ZH", "AG"],
            languages=["DE", "EN"],
            parties=[party],
            deadlines=[deadline],
            legal_issues=[issue],
            facts=["Fact 1", "Fact 2"],
            tags=["important", "urgent"],
            notes="This is a test case",
        )

        assert context.case_type == CaseType.LITIGATION
        assert context.firm_id == "test-firm"
        assert len(context.parties) == 1
        assert len(context.deadlines) == 1
        assert len(context.legal_issues) == 1
        assert "important" in context.tags

    def test_context_to_dict(self) -> None:
        """Test context serialization."""
        party = Party(name="Test Party", role="plaintiff")
        context = ManagedCaseContext(
            case_id="SERIAL-001",
            title="Serialization Test",
            case_type=CaseType.CONTRACT,
            parties=[party],
        )

        data = context.to_dict()

        assert data["case_id"] == "SERIAL-001"
        assert data["title"] == "Serialization Test"
        assert data["case_type"] == "contract"
        assert data["status"] == "active"
        assert len(data["parties"]) == 1
        assert "jurisdiction" in data
        assert data["jurisdiction"]["federal"] is True

    def test_context_from_dict(self) -> None:
        """Test context deserialization."""
        data = {
            "case_id": "DESER-001",
            "title": "Deserialization Test",
            "case_type": "litigation",
            "status": "archived",
            "firm_id": "firm-123",
            "created_by": "user-456",
            "jurisdiction": {
                "federal": False,
                "cantons": ["BE", "FR"],
                "languages": ["FR", "DE"],
            },
            "parties": [{"name": "Party A", "role": "defendant"}],
            "created_at": "2025-01-15T10:00:00",
            "updated_at": "2025-02-20T15:30:00",
            "facts": ["Fact A", "Fact B"],
            "legal_issues": [],
            "agent_history": [],
            "findings": [],
            "documents": [],
            "deadlines": [],
            "milestones": [],
            "tags": ["test"],
            "notes": "Test notes",
            "metadata": {},
        }

        context = ManagedCaseContext.from_dict(data)

        assert context.case_id == "DESER-001"
        assert context.case_type == CaseType.LITIGATION
        assert context.status == CaseStatus.ARCHIVED
        assert context.jurisdiction_federal is False
        assert "BE" in context.jurisdiction_cantons
        assert len(context.parties) == 1
        assert len(context.facts) == 2

    def test_context_to_agent_context(self) -> None:
        """Test conversion to lightweight agent context."""
        party = Party(name="Client", role="client")
        issue = LegalIssue(description="Issue 1", legal_area="OR")
        execution = AgentExecution(
            agent_id="researcher",
            timestamp=datetime.utcnow(),
            task="Research",
            outcome="success",
        )

        context = ManagedCaseContext(
            case_id="AGENT-CTX-001",
            title="Agent Context Test",
            case_type=CaseType.CORPORATE,
            parties=[party],
            legal_issues=[issue],
            agent_history=[execution],
        )

        agent_ctx = context.to_agent_context()

        assert agent_ctx["case_id"] == "AGENT-CTX-001"
        assert agent_ctx["case_type"] == "corporate"
        assert len(agent_ctx["parties"]) == 1
        assert len(agent_ctx["legal_issues"]) == 1
        assert "researcher" in agent_ctx["agent_history"]


# =============================================================================
# CaseManager Tests
# =============================================================================


class TestCaseManagerCreation:
    """Test CaseManager case creation."""

    @pytest.mark.asyncio
    async def test_create_case_minimal(self, case_manager: CaseManager) -> None:
        """Test creating a case with minimal fields."""
        case = await case_manager.create_case(
            title="Simple Test Case",
        )

        assert case.title == "Simple Test Case"
        assert case.case_type == CaseType.OTHER
        assert case.status == CaseStatus.ACTIVE
        assert case.case_id is not None
        assert case_manager.current_case == case

    @pytest.mark.asyncio
    async def test_create_case_full(self, case_manager: CaseManager) -> None:
        """Test creating a case with all fields."""
        party = Party(name="Hans Müller", role="client")

        case = await case_manager.create_case(
            title="Müller vs. ABC AG",
            case_type=CaseType.LITIGATION,
            jurisdiction_federal=False,
            jurisdiction_cantons=["ZH"],
            languages=["DE", "FR"],
            parties=[party],
            facts=["Contract signed 2024-01-15"],
            user_id="lawyer-001",
            firm_id="firm-001",
            tags=["priority"],
            notes="Important case",
        )

        assert case.title == "Müller vs. ABC AG"
        assert case.case_type == CaseType.LITIGATION
        assert case.jurisdiction_federal is False
        assert "ZH" in case.jurisdiction_cantons
        assert len(case.parties) == 1
        assert len(case.facts) == 1
        assert case.firm_id == "firm-001"

    @pytest.mark.asyncio
    async def test_case_id_generation(self, case_manager: CaseManager) -> None:
        """Test that case IDs are generated correctly."""
        case = await case_manager.create_case(title="Test ID Generation")

        # ID should follow format: PREFIX-YEAR-SUFFIX
        parts = case.case_id.split("-")
        assert len(parts) == 3
        assert parts[0] == "TES"  # First 3 chars of "Test"
        assert parts[1] == str(datetime.utcnow().year)


class TestCaseManagerOperations:
    """Test CaseManager case operations."""

    @pytest.mark.asyncio
    async def test_open_case(self, case_manager: CaseManager) -> None:
        """Test opening an existing case."""
        created = await case_manager.create_case(title="Open Test")
        case_id = created.case_id

        # Clear current case
        case_manager._current_case = None

        # Open the case
        opened = await case_manager.open_case(case_id)

        assert opened is not None
        assert opened.case_id == case_id
        assert opened.title == "Open Test"
        assert case_manager.current_case == opened

    @pytest.mark.asyncio
    async def test_open_nonexistent_case(self, case_manager: CaseManager) -> None:
        """Test opening a case that doesn't exist."""
        result = await case_manager.open_case("NONEXISTENT-001")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_case(self, case_manager: CaseManager) -> None:
        """Test saving a case."""
        case = await case_manager.create_case(title="Save Test")
        original_updated = case.updated_at

        # Modify the case
        case.notes = "Updated notes"

        # Save
        success = await case_manager.save_case(case)

        assert success is True
        assert case.updated_at > original_updated

    @pytest.mark.asyncio
    async def test_close_case(self, case_manager: CaseManager) -> None:
        """Test closing a case."""
        case = await case_manager.create_case(title="Close Test")
        case_id = case.case_id

        success = await case_manager.close_case(case_id, reason="Settled")

        assert success is True

        # Reopen to verify
        closed_case = await case_manager.open_case(case_id)
        assert closed_case is not None
        assert closed_case.status == CaseStatus.CLOSED
        assert closed_case.closed_at is not None
        assert "Settled" in closed_case.notes

    @pytest.mark.asyncio
    async def test_close_current_case(self, case_manager: CaseManager) -> None:
        """Test closing the current case without specifying ID."""
        _case = await case_manager.create_case(title="Close Current Test")  # noqa: F841

        success = await case_manager.close_case()

        assert success is True
        assert case_manager.current_case is None

    @pytest.mark.asyncio
    async def test_archive_case(self, case_manager: CaseManager) -> None:
        """Test archiving a case."""
        case = await case_manager.create_case(title="Archive Test")
        case_id = case.case_id

        success = await case_manager.archive_case(case_id)

        assert success is True

        # Verify
        archived = await case_manager.open_case(case_id)
        assert archived is not None
        assert archived.status == CaseStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_list_cases(self, case_manager: CaseManager) -> None:
        """Test listing cases."""
        await case_manager.create_case(title="List Test 1")
        await case_manager.create_case(title="List Test 2")
        await case_manager.create_case(title="List Test 3")

        cases = await case_manager.list_cases()

        assert len(cases) == 3

    @pytest.mark.asyncio
    async def test_list_cases_with_status_filter(self, case_manager: CaseManager) -> None:
        """Test listing cases filtered by status."""
        _case1 = await case_manager.create_case(title="Active Case")  # noqa: F841
        case2 = await case_manager.create_case(title="To Archive")

        await case_manager.archive_case(case2.case_id)

        active_cases = await case_manager.list_cases(status=CaseStatus.ACTIVE)
        archived_cases = await case_manager.list_cases(status=CaseStatus.ARCHIVED)

        assert len(active_cases) == 1
        assert len(archived_cases) == 1

    @pytest.mark.asyncio
    async def test_list_cases_pagination(self, case_manager: CaseManager) -> None:
        """Test listing cases with pagination."""
        for i in range(5):
            await case_manager.create_case(title=f"Page Test {i}")

        first_page = await case_manager.list_cases(limit=2, offset=0)
        second_page = await case_manager.list_cases(limit=2, offset=2)

        assert len(first_page) == 2
        assert len(second_page) == 2


class TestCaseManagerSummary:
    """Test CaseManager summary generation."""

    @pytest.mark.asyncio
    async def test_generate_summary(self, case_manager: CaseManager) -> None:
        """Test generating a case summary."""
        party = Party(name="Client", role="client")
        case = await case_manager.create_case(
            title="Summary Test",
            parties=[party],
            facts=["Fact 1", "Fact 2"],
        )

        summary = await case_manager.generate_summary(case.case_id)

        assert summary["case_id"] == case.case_id
        assert summary["title"] == "Summary Test"
        assert summary["parties_count"] == 1
        assert summary["facts_count"] == 2

    @pytest.mark.asyncio
    async def test_generate_summary_with_deadlines(self, case_manager: CaseManager) -> None:
        """Test summary includes deadline statistics."""
        case = await case_manager.create_case(title="Deadline Summary Test")

        # Add deadlines
        future_deadline = Deadline(
            name="Future",
            due_date=datetime.utcnow() + timedelta(days=30),
        )
        past_deadline = Deadline(
            name="Overdue",
            due_date=datetime.utcnow() - timedelta(days=5),
        )

        await case_manager.add_deadline(case.case_id, future_deadline)
        await case_manager.add_deadline(case.case_id, past_deadline)

        summary = await case_manager.generate_summary(case.case_id)

        assert summary["deadlines"]["total"] == 2
        assert summary["deadlines"]["overdue"] == 1

    @pytest.mark.asyncio
    async def test_generate_summary_nonexistent(self, case_manager: CaseManager) -> None:
        """Test summary for nonexistent case."""
        summary = await case_manager.generate_summary("NONEXISTENT-001")

        assert "error" in summary


class TestCaseManagerExport:
    """Test CaseManager export functionality."""

    @pytest.mark.asyncio
    async def test_export_json(self, case_manager: CaseManager) -> None:
        """Test exporting case as JSON."""
        party = Party(name="Export Client", role="client")
        case = await case_manager.create_case(
            title="Export Test",
            parties=[party],
        )

        exported = await case_manager.export_case(case.case_id, format="json")

        data = json.loads(exported)
        assert data["case_id"] == case.case_id
        assert data["title"] == "Export Test"
        assert len(data["parties"]) == 1

    @pytest.mark.asyncio
    async def test_export_markdown(self, case_manager: CaseManager) -> None:
        """Test exporting case as Markdown."""
        party = Party(name="MD Client", role="plaintiff")
        issue = LegalIssue(
            description="Contract breach",
            legal_area="OR",
            relevant_articles=["Art. 97 OR"],
        )

        case = await case_manager.create_case(
            title="Markdown Export Test",
            case_type=CaseType.LITIGATION,
            parties=[party],
            facts=["Contract signed", "Breach occurred"],
        )
        await case_manager.add_legal_issue(case.case_id, issue)

        exported = await case_manager.export_case(case.case_id, format="markdown")

        assert "# Case: Markdown Export Test" in exported
        assert "**Case ID**" in exported
        assert "## Parties" in exported
        assert "MD Client" in exported
        assert "## Facts" in exported
        assert "Contract breach" in exported

    @pytest.mark.asyncio
    async def test_export_nonexistent_case(self, case_manager: CaseManager) -> None:
        """Test export for nonexistent case."""
        result = await case_manager.export_case("NONEXISTENT", format="json")

        assert "error" in result


class TestCaseManagerContentModification:
    """Test CaseManager content modification methods."""

    @pytest.mark.asyncio
    async def test_add_party(self, case_manager: CaseManager) -> None:
        """Test adding a party to a case."""
        case = await case_manager.create_case(title="Add Party Test")

        party = Party(name="New Party", role="witness")
        success = await case_manager.add_party(case.case_id, party)

        assert success is True

        # Verify
        updated = await case_manager.open_case(case.case_id)
        assert updated is not None
        assert len(updated.parties) == 1
        assert updated.parties[0].name == "New Party"

    @pytest.mark.asyncio
    async def test_add_fact(self, case_manager: CaseManager) -> None:
        """Test adding a fact to a case."""
        case = await case_manager.create_case(title="Add Fact Test")

        success = await case_manager.add_fact(case.case_id, "Contract was signed on 2024-01-15")

        assert success is True

        updated = await case_manager.open_case(case.case_id)
        assert updated is not None
        assert "Contract was signed" in updated.facts[0]

    @pytest.mark.asyncio
    async def test_add_legal_issue(self, case_manager: CaseManager) -> None:
        """Test adding a legal issue to a case."""
        case = await case_manager.create_case(title="Add Issue Test")

        issue = LegalIssue(
            description="Statute of limitations question",
            legal_area="OR",
            relevant_articles=["Art. 127 OR"],
        )
        success = await case_manager.add_legal_issue(case.case_id, issue)

        assert success is True

        updated = await case_manager.open_case(case.case_id)
        assert updated is not None
        assert len(updated.legal_issues) == 1

    @pytest.mark.asyncio
    async def test_add_deadline(self, case_manager: CaseManager) -> None:
        """Test adding a deadline to a case."""
        case = await case_manager.create_case(title="Add Deadline Test")

        deadline = Deadline(
            name="File response",
            due_date=datetime.utcnow() + timedelta(days=14),
            description="Response to motion",
        )
        success = await case_manager.add_deadline(case.case_id, deadline)

        assert success is True

        updated = await case_manager.open_case(case.case_id)
        assert updated is not None
        assert len(updated.deadlines) == 1
        assert updated.deadlines[0].name == "File response"

    @pytest.mark.asyncio
    async def test_add_finding(self, case_manager: CaseManager) -> None:
        """Test adding a finding to a case."""
        case = await case_manager.create_case(title="Add Finding Test")

        finding = Finding(
            content="Relevant precedent found: BGE 147 IV 73",
            source="researcher",
            category="precedent",
            confidence=0.9,
        )
        success = await case_manager.add_finding(case.case_id, finding)

        assert success is True

        updated = await case_manager.open_case(case.case_id)
        assert updated is not None
        assert len(updated.findings) == 1
        assert "BGE 147 IV 73" in updated.findings[0].content

    @pytest.mark.asyncio
    async def test_add_document(self, case_manager: CaseManager) -> None:
        """Test adding a document reference to a case."""
        case = await case_manager.create_case(title="Add Document Test")

        doc = DocumentRef(
            name="Main Contract",
            path="/documents/contract.pdf",
            document_type="contract",
        )
        success = await case_manager.add_document(case.case_id, doc)

        assert success is True

        updated = await case_manager.open_case(case.case_id)
        assert updated is not None
        assert len(updated.documents) == 1
        assert updated.documents[0].name == "Main Contract"

    @pytest.mark.asyncio
    async def test_record_agent_execution(self, case_manager: CaseManager) -> None:
        """Test recording an agent execution."""
        case = await case_manager.create_case(title="Agent Execution Test")

        execution = AgentExecution(
            agent_id="researcher",
            timestamp=datetime.utcnow(),
            task="Research Swiss contract law precedents",
            outcome="success",
            summary="Found 5 relevant decisions",
        )
        success = await case_manager.record_agent_execution(case.case_id, execution)

        assert success is True

        updated = await case_manager.open_case(case.case_id)
        assert updated is not None
        assert len(updated.agent_history) == 1
        assert updated.agent_history[0].agent_id == "researcher"

    @pytest.mark.asyncio
    async def test_add_to_current_case(self, case_manager: CaseManager) -> None:
        """Test adding content to current case without specifying ID."""
        _case = await case_manager.create_case(title="Current Case Test")  # noqa: F841

        # Add without specifying case_id (should use current)
        success = await case_manager.add_fact(None, "Fact for current case")

        assert success is True
        assert case_manager.current_case is not None
        assert len(case_manager.current_case.facts) == 1

    @pytest.mark.asyncio
    async def test_add_to_no_case(self, case_manager: CaseManager) -> None:
        """Test adding content when no case is active."""
        # Ensure no current case
        case_manager._current_case = None

        success = await case_manager.add_fact(None, "Orphan fact")

        assert success is False


class TestCaseManagerEdgeCases:
    """Test CaseManager edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_close_no_case_specified(self, case_manager: CaseManager) -> None:
        """Test closing when no case is specified or active."""
        case_manager._current_case = None

        success = await case_manager.close_case()

        assert success is False

    @pytest.mark.asyncio
    async def test_archive_no_case_specified(self, case_manager: CaseManager) -> None:
        """Test archiving when no case is specified or active."""
        case_manager._current_case = None

        success = await case_manager.archive_case()

        assert success is False

    @pytest.mark.asyncio
    async def test_save_no_case(self, case_manager: CaseManager) -> None:
        """Test saving when no case is specified."""
        case_manager._current_case = None

        success = await case_manager.save_case()

        assert success is False

    @pytest.mark.asyncio
    async def test_export_invalid_format(self, case_manager: CaseManager) -> None:
        """Test export with invalid format."""
        case = await case_manager.create_case(title="Invalid Format Test")

        result = await case_manager.export_case(case.case_id, format="xml")

        assert "error" in result
        assert "Unsupported format" in result
