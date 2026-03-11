"""
Unit tests for Agent Base Classes

Tests the AgentBase, CaseContext, and related data classes from src/agents/base.py
"""

from datetime import datetime
from typing import Any

import pytest

from src.agents.base import (
    ActionType,
    AgentAction,
    AgentAuditLog,
    AgentBase,
    AgentOutcome,
    AgentResult,
    AutonomyMode,
    CaseContext,
    Checkpoint,
    Party,
)


class TestAutonomyMode:
    """Test AutonomyMode enum."""

    def test_enum_values(self) -> None:
        """Test autonomy mode enum has correct values."""
        assert AutonomyMode.CAUTIOUS.value == "cautious"
        assert AutonomyMode.BALANCED.value == "balanced"
        assert AutonomyMode.AUTONOMOUS.value == "autonomous"

    def test_enum_from_string(self) -> None:
        """Test creating enum from string value."""
        assert AutonomyMode("cautious") == AutonomyMode.CAUTIOUS
        assert AutonomyMode("balanced") == AutonomyMode.BALANCED
        assert AutonomyMode("autonomous") == AutonomyMode.AUTONOMOUS


class TestAgentOutcome:
    """Test AgentOutcome enum."""

    def test_enum_values(self) -> None:
        """Test outcome enum has correct values."""
        assert AgentOutcome.SUCCESS.value == "success"
        assert AgentOutcome.PARTIAL.value == "partial"
        assert AgentOutcome.FAILED.value == "failed"
        assert AgentOutcome.CANCELLED.value == "cancelled"


class TestActionType:
    """Test ActionType enum."""

    def test_enum_values(self) -> None:
        """Test action type enum has correct values."""
        assert ActionType.SEARCH.value == "search"
        assert ActionType.ANALYZE.value == "analyze"
        assert ActionType.GENERATE.value == "generate"
        assert ActionType.INVOKE_AGENT.value == "invoke_agent"
        assert ActionType.CHECKPOINT.value == "checkpoint"
        assert ActionType.USER_CONFIRM.value == "user_confirm"


class TestParty:
    """Test Party data class."""

    def test_create_party(self) -> None:
        """Test creating a party."""
        party = Party(name="Hans Müller", role="client")

        assert party.name == "Hans Müller"
        assert party.role == "client"
        assert party.contact is None
        assert party.metadata == {}

    def test_create_party_with_all_fields(self) -> None:
        """Test creating a party with all fields."""
        party = Party(
            name="ABC AG",
            role="defendant",
            contact="info@abc.ch",
            metadata={"address": "Zürich"},
        )

        assert party.name == "ABC AG"
        assert party.role == "defendant"
        assert party.contact == "info@abc.ch"
        assert party.metadata["address"] == "Zürich"


class TestCaseContext:
    """Test CaseContext data class."""

    def test_create_case_context(self) -> None:
        """Test creating a case context with minimal fields."""
        context = CaseContext(
            case_id="TEST-2025-001",
            title="Test Case",
            case_type="litigation",
        )

        assert context.case_id == "TEST-2025-001"
        assert context.title == "Test Case"
        assert context.case_type == "litigation"
        assert context.jurisdiction_federal is True
        assert context.jurisdiction_cantons == []
        assert context.languages == ["DE"]
        assert context.parties == []
        assert context.facts == []
        assert context.legal_issues == []
        assert context.agent_history == []
        assert context.findings == {}

    def test_create_case_context_with_all_fields(self) -> None:
        """Test creating a case context with all fields."""
        party = Party(name="Client", role="client")
        context = CaseContext(
            case_id="TEST-2025-002",
            title="Full Test Case",
            case_type="corporate",
            jurisdiction_federal=False,
            jurisdiction_cantons=["ZH", "BE"],
            languages=["DE", "FR"],
            parties=[party],
            facts=["Fact 1", "Fact 2"],
            legal_issues=["Issue 1"],
            agent_history=["researcher"],
            findings={"key": "value"},
        )

        assert context.jurisdiction_federal is False
        assert context.jurisdiction_cantons == ["ZH", "BE"]
        assert context.languages == ["DE", "FR"]
        assert len(context.parties) == 1
        assert context.parties[0].name == "Client"
        assert context.facts == ["Fact 1", "Fact 2"]
        assert context.legal_issues == ["Issue 1"]
        assert context.agent_history == ["researcher"]
        assert context.findings == {"key": "value"}

    def test_case_context_to_dict(self) -> None:
        """Test serializing case context to dictionary."""
        party = Party(name="Test Party", role="plaintiff")
        context = CaseContext(
            case_id="TEST-2025-003",
            title="Serialization Test",
            case_type="contract",
            parties=[party],
            facts=["Test fact"],
        )

        data = context.to_dict()

        assert data["case_id"] == "TEST-2025-003"
        assert data["title"] == "Serialization Test"
        assert data["case_type"] == "contract"
        assert data["jurisdiction"]["federal"] is True
        assert data["jurisdiction"]["cantons"] == []
        assert data["jurisdiction"]["languages"] == ["DE"]
        assert len(data["parties"]) == 1
        assert data["parties"][0]["name"] == "Test Party"
        assert data["facts"] == ["Test fact"]
        assert "created_at" in data


class TestAgentAction:
    """Test AgentAction data class."""

    def test_create_action_factory(self) -> None:
        """Test creating an action using the factory method."""
        action = AgentAction.create(
            action_type=ActionType.SEARCH,
            description="Searched for precedents",
            inputs={"query": "BGE 147 IV 73"},
            outputs={"results": 5},
            duration_ms=1500,
        )

        assert action.action_type == ActionType.SEARCH
        assert action.description == "Searched for precedents"
        assert action.inputs == {"query": "BGE 147 IV 73"}
        assert action.outputs == {"results": 5}
        assert action.duration_ms == 1500
        assert action.sub_agent_id is None
        assert action.action_id is not None
        assert action.timestamp is not None

    def test_create_action_with_sub_agent(self) -> None:
        """Test creating an action for a sub-agent invocation."""
        action = AgentAction.create(
            action_type=ActionType.INVOKE_AGENT,
            description="Invoked citation-checker",
            inputs={"task": "verify citations"},
            outputs={"verified": 3},
            duration_ms=5000,
            sub_agent_id="citation-checker",
        )

        assert action.action_type == ActionType.INVOKE_AGENT
        assert action.sub_agent_id == "citation-checker"


class TestCheckpoint:
    """Test Checkpoint data class."""

    def test_create_checkpoint_factory(self) -> None:
        """Test creating a checkpoint using the factory method."""
        state = {"step": "analysis", "progress": 50}
        checkpoint = Checkpoint.create(
            checkpoint_type="auto",
            state=state,
            description="Midway checkpoint",
        )

        assert checkpoint.checkpoint_type == "auto"
        assert checkpoint.state == state
        assert checkpoint.description == "Midway checkpoint"
        assert checkpoint.checkpoint_id is not None
        assert checkpoint.timestamp is not None

    def test_checkpoint_types(self) -> None:
        """Test different checkpoint types."""
        types = ["auto", "user", "pre_external", "pre_subagent"]

        for cp_type in types:
            checkpoint = Checkpoint.create(
                checkpoint_type=cp_type,
                state={},
                description=f"{cp_type} checkpoint",
            )
            assert checkpoint.checkpoint_type == cp_type


class TestAgentAuditLog:
    """Test AgentAuditLog data class."""

    def test_create_audit_log(self) -> None:
        """Test creating an audit log."""
        action = AgentAction.create(
            action_type=ActionType.SEARCH,
            description="Test action",
            inputs={},
            outputs={},
            duration_ms=100,
        )
        checkpoint = Checkpoint.create("auto", {}, "Test checkpoint")

        audit_log = AgentAuditLog(
            log_id="test-log-001",
            timestamp=datetime.utcnow(),
            case_id="TEST-2025-001",
            user_id="test-user",
            firm_id="test-firm",
            agent_id="test-agent",
            agent_version="1.0.0",
            autonomy_mode=AutonomyMode.BALANCED,
            actions=[action],
            sources_accessed=["BGer", "BGE"],
            documents_read=["doc1.pdf"],
            documents_written=["output.md"],
            outcome=AgentOutcome.SUCCESS,
            deliverables=["Research report"],
            errors=[],
            checkpoints=[checkpoint],
        )

        assert audit_log.log_id == "test-log-001"
        assert audit_log.case_id == "TEST-2025-001"
        assert audit_log.agent_id == "test-agent"
        assert audit_log.outcome == AgentOutcome.SUCCESS
        assert len(audit_log.actions) == 1
        assert len(audit_log.checkpoints) == 1

    def test_audit_log_to_dict(self) -> None:
        """Test serializing audit log to dictionary."""
        action = AgentAction.create(
            action_type=ActionType.ANALYZE,
            description="Analysis",
            inputs={"data": "test"},
            outputs={"result": "done"},
            duration_ms=500,
        )

        audit_log = AgentAuditLog(
            log_id="test-log-002",
            timestamp=datetime.utcnow(),
            case_id="TEST-2025-002",
            user_id="user",
            firm_id="firm",
            agent_id="agent",
            agent_version="2.0.0",
            autonomy_mode=AutonomyMode.CAUTIOUS,
            actions=[action],
            sources_accessed=[],
            documents_read=[],
            documents_written=[],
            outcome=AgentOutcome.PARTIAL,
            deliverables=[],
            errors=[{"type": "TestError", "message": "Test"}],
            checkpoints=[],
        )

        data = audit_log.to_dict()

        assert data["log_id"] == "test-log-002"
        assert data["case_id"] == "TEST-2025-002"
        assert data["autonomy_mode"] == "cautious"
        assert data["outcome"] == "partial"
        assert len(data["actions"]) == 1
        assert data["actions"][0]["type"] == "analyze"


class TestAgentResult:
    """Test AgentResult data class."""

    def test_create_success_result(self) -> None:
        """Test creating a successful agent result."""
        audit_log = AgentAuditLog(
            log_id="log-001",
            timestamp=datetime.utcnow(),
            case_id="case-001",
            user_id="user",
            firm_id="firm",
            agent_id="agent",
            agent_version="1.0.0",
            autonomy_mode=AutonomyMode.BALANCED,
            actions=[],
            sources_accessed=[],
            documents_read=[],
            documents_written=[],
            outcome=AgentOutcome.SUCCESS,
            deliverables=["Report"],
            errors=[],
            checkpoints=[],
        )

        result: AgentResult[str] = AgentResult(
            success=True,
            outcome=AgentOutcome.SUCCESS,
            deliverable="Research Report Content",
            partial_results=None,
            error_message=None,
            audit_log=audit_log,
            execution_time_ms=5000,
        )

        assert result.success is True
        assert result.outcome == AgentOutcome.SUCCESS
        assert result.deliverable == "Research Report Content"
        assert result.error_message is None

    def test_create_failed_result(self) -> None:
        """Test creating a failed agent result."""
        audit_log = AgentAuditLog(
            log_id="log-002",
            timestamp=datetime.utcnow(),
            case_id="case-001",
            user_id="user",
            firm_id="firm",
            agent_id="agent",
            agent_version="1.0.0",
            autonomy_mode=AutonomyMode.AUTONOMOUS,
            actions=[],
            sources_accessed=[],
            documents_read=[],
            documents_written=[],
            outcome=AgentOutcome.FAILED,
            deliverables=[],
            errors=[{"type": "Error", "message": "Connection failed"}],
            checkpoints=[],
        )

        result: AgentResult[str] = AgentResult(
            success=False,
            outcome=AgentOutcome.FAILED,
            deliverable=None,
            partial_results="Partial data before failure",
            error_message="Connection failed",
            audit_log=audit_log,
            execution_time_ms=1000,
        )

        assert result.success is False
        assert result.outcome == AgentOutcome.FAILED
        assert result.deliverable is None
        assert result.partial_results == "Partial data before failure"
        assert result.error_message == "Connection failed"

    def test_result_to_dict(self) -> None:
        """Test serializing result to dictionary."""
        audit_log = AgentAuditLog(
            log_id="log-003",
            timestamp=datetime.utcnow(),
            case_id="case-001",
            user_id="user",
            firm_id="firm",
            agent_id="agent",
            agent_version="1.0.0",
            autonomy_mode=AutonomyMode.BALANCED,
            actions=[],
            sources_accessed=[],
            documents_read=[],
            documents_written=[],
            outcome=AgentOutcome.SUCCESS,
            deliverables=[],
            errors=[],
            checkpoints=[],
        )

        result: AgentResult[dict[str, str]] = AgentResult(
            success=True,
            outcome=AgentOutcome.SUCCESS,
            deliverable={"key": "value"},
            partial_results=None,
            error_message=None,
            audit_log=audit_log,
            execution_time_ms=2000,
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["outcome"] == "success"
        assert data["deliverable"] == {"key": "value"}
        assert data["execution_time_ms"] == 2000
        assert data["audit_log_id"] == "log-003"


# =============================================================================
# Test Agent Implementation
# =============================================================================


class TestAgent(AgentBase):
    """Concrete implementation of AgentBase for testing."""

    @property
    def agent_id(self) -> str:
        return "test-agent"

    @property
    def agent_version(self) -> str:
        return "1.0.0"

    async def execute(self, task: str, **kwargs: Any) -> AgentResult[str]:
        """Simple test execution."""
        self._start_time = datetime.utcnow()

        # Record an action
        self._record_action(
            ActionType.ANALYZE,
            f"Analyzing: {task}",
            inputs={"task": task},
            outputs={"status": "completed"},
            duration_ms=100,
        )

        # Create audit log
        audit_log = self._create_audit_log(
            outcome=AgentOutcome.SUCCESS,
            deliverables=["Test result"],
        )

        return AgentResult(
            success=True,
            outcome=AgentOutcome.SUCCESS,
            deliverable=f"Completed: {task}",
            partial_results=None,
            error_message=None,
            audit_log=audit_log,
            execution_time_ms=100,
        )


class TestAgentBase:
    """Test AgentBase class functionality."""

    def test_agent_initialization_default(self) -> None:
        """Test agent initializes with default values."""
        agent = TestAgent()

        assert agent.autonomy_mode == AutonomyMode.BALANCED
        assert agent.case_context is None
        assert agent.user_id == "anonymous"
        assert agent.firm_id == "default"

    def test_agent_initialization_custom(self) -> None:
        """Test agent initializes with custom values."""
        case_context = CaseContext(
            case_id="TEST-001",
            title="Test Case",
            case_type="litigation",
        )

        agent = TestAgent(
            autonomy_mode=AutonomyMode.CAUTIOUS,
            case_context=case_context,
            user_id="test-user",
            firm_id="test-firm",
        )

        assert agent.autonomy_mode == AutonomyMode.CAUTIOUS
        assert agent.case_context is not None
        assert agent.case_context.case_id == "TEST-001"
        assert agent.user_id == "test-user"
        assert agent.firm_id == "test-firm"

    def test_agent_properties(self) -> None:
        """Test agent abstract properties."""
        agent = TestAgent()

        assert agent.agent_id == "test-agent"
        assert agent.agent_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_agent_execute(self) -> None:
        """Test agent execution."""
        agent = TestAgent()
        result = await agent.execute("Test task")

        assert result.success is True
        assert result.outcome == AgentOutcome.SUCCESS
        assert result.deliverable is not None and "Test task" in result.deliverable
        assert result.audit_log is not None
        assert result.audit_log.agent_id == "test-agent"

    # -------------------------------------------------------------------------
    # Checkpoint Tests
    # -------------------------------------------------------------------------

    def test_create_checkpoint(self) -> None:
        """Test creating a checkpoint."""
        agent = TestAgent()
        agent.update_state("step", "analysis")
        agent.update_state("progress", 50)

        checkpoint = agent.create_checkpoint("user", "User-requested checkpoint")

        assert checkpoint.checkpoint_type == "user"
        assert checkpoint.description == "User-requested checkpoint"
        assert checkpoint.state["step"] == "analysis"
        assert checkpoint.state["progress"] == 50

    def test_restore_checkpoint(self) -> None:
        """Test restoring from a checkpoint."""
        agent = TestAgent()
        agent.update_state("step", "initial")

        # Create checkpoint
        checkpoint = agent.create_checkpoint("auto", "Before change")

        # Modify state
        agent.update_state("step", "modified")
        assert agent.get_state("step") == "modified"

        # Restore checkpoint
        success = agent.restore_checkpoint(checkpoint.checkpoint_id)

        assert success is True
        assert agent.get_state("step") == "initial"

    def test_restore_nonexistent_checkpoint(self) -> None:
        """Test restoring from a nonexistent checkpoint."""
        agent = TestAgent()

        success = agent.restore_checkpoint("nonexistent-id")

        assert success is False

    def test_get_latest_checkpoint(self) -> None:
        """Test getting the latest checkpoint."""
        agent = TestAgent()

        # No checkpoints yet
        assert agent.get_latest_checkpoint() is None

        # Create checkpoints
        agent.create_checkpoint("auto", "First")
        agent.create_checkpoint("auto", "Second")
        latest = agent.get_latest_checkpoint()

        assert latest is not None
        assert latest.description == "Second"

    # -------------------------------------------------------------------------
    # State Management Tests
    # -------------------------------------------------------------------------

    def test_update_and_get_state(self) -> None:
        """Test updating and getting state."""
        agent = TestAgent()

        agent.update_state("key1", "value1")
        agent.update_state("key2", 42)
        agent.update_state("key3", {"nested": "data"})

        assert agent.get_state("key1") == "value1"
        assert agent.get_state("key2") == 42
        assert agent.get_state("key3") == {"nested": "data"}

    def test_get_state_default(self) -> None:
        """Test getting state with default value."""
        agent = TestAgent()

        assert agent.get_state("nonexistent") is None
        assert agent.get_state("nonexistent", "default") == "default"

    # -------------------------------------------------------------------------
    # Source and Document Recording Tests
    # -------------------------------------------------------------------------

    def test_record_source_access(self) -> None:
        """Test recording source access."""
        agent = TestAgent()

        agent.record_source_access("BGer")
        agent.record_source_access("BGE Database")

        assert "BGer" in agent._sources_accessed
        assert "BGE Database" in agent._sources_accessed

    def test_record_document_read(self) -> None:
        """Test recording document read."""
        agent = TestAgent()

        agent.record_document_read("contract.pdf")
        agent.record_document_read("brief.docx")

        assert "contract.pdf" in agent._documents_read
        assert "brief.docx" in agent._documents_read

    def test_record_document_write(self) -> None:
        """Test recording document write."""
        agent = TestAgent()

        agent.record_document_write("analysis.md")
        agent.record_document_write("report.pdf")

        assert "analysis.md" in agent._documents_written
        assert "report.pdf" in agent._documents_written

    # -------------------------------------------------------------------------
    # Input Sanitization Tests
    # -------------------------------------------------------------------------

    def test_sanitize_inputs_redacts_sensitive(self) -> None:
        """Test that sensitive inputs are redacted."""
        agent = TestAgent()

        inputs = {
            "query": "test query",
            "password": "secret123",
            "api_token": "tok_abc",
            "secret_key": "sk_xyz",
        }

        sanitized = agent._sanitize_inputs(inputs)

        assert sanitized["query"] == "test query"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["api_token"] == "[REDACTED]"
        assert sanitized["secret_key"] == "[REDACTED]"

    def test_sanitize_inputs_truncates_long_strings(self) -> None:
        """Test that long strings are truncated."""
        agent = TestAgent()

        long_string = "x" * 2000
        inputs = {"content": long_string}

        sanitized = agent._sanitize_inputs(inputs)

        assert len(sanitized["content"]) < len(long_string)
        assert sanitized["content"].endswith("...[truncated]")

    # -------------------------------------------------------------------------
    # Output Summarization Tests
    # -------------------------------------------------------------------------

    def test_summarize_outputs_lists(self) -> None:
        """Test summarizing list outputs."""
        agent = TestAgent()

        outputs = {"results": [1, 2, 3, 4, 5]}

        summarized = agent._summarize_outputs(outputs)

        assert summarized["results"] == "[List with 5 items]"

    def test_summarize_outputs_dicts(self) -> None:
        """Test summarizing dict outputs."""
        agent = TestAgent()

        outputs = {"data": {"a": 1, "b": 2, "c": 3}}

        summarized = agent._summarize_outputs(outputs)

        assert summarized["data"] == "[Dict with 3 keys]"

    def test_summarize_outputs_truncates_strings(self) -> None:
        """Test that long string outputs are truncated."""
        agent = TestAgent()

        long_string = "y" * 1000
        outputs = {"text": long_string}

        summarized = agent._summarize_outputs(outputs)

        assert len(summarized["text"]) < len(long_string)
        assert summarized["text"].endswith("...[truncated]")

    # -------------------------------------------------------------------------
    # Error Handling Tests
    # -------------------------------------------------------------------------

    def test_handle_recoverable_error(self) -> None:
        """Test handling a recoverable error."""
        agent = TestAgent()
        agent.autonomy_mode = AutonomyMode.AUTONOMOUS

        error = ValueError("Test error")
        agent._handle_error(error, recoverable=True)

        assert len(agent._errors) == 1
        assert agent._errors[0]["type"] == "ValueError"
        assert agent._errors[0]["message"] == "Test error"
        assert agent._errors[0]["recoverable"] is True
        # Autonomy mode should be escalated to cautious
        assert agent.autonomy_mode == AutonomyMode.CAUTIOUS

    def test_handle_non_recoverable_error(self) -> None:
        """Test handling a non-recoverable error."""
        agent = TestAgent()
        initial_mode = agent.autonomy_mode

        error = RuntimeError("Critical error")
        agent._handle_error(error, recoverable=False)

        assert len(agent._errors) == 1
        assert agent._errors[0]["recoverable"] is False
        # Autonomy mode should NOT change for non-recoverable errors
        assert agent.autonomy_mode == initial_mode

    def test_create_partial_result(self) -> None:
        """Test creating a partial result."""
        agent = TestAgent()

        # Create a checkpoint first
        agent.update_state("progress", 75)
        checkpoint = agent.create_checkpoint("auto", "Before failure")

        # Record some actions
        agent._record_action(
            ActionType.SEARCH,
            "Search completed",
            inputs={},
            outputs={},
            duration_ms=100,
        )

        partial = agent._create_partial_result({"partial": "data"})

        assert partial["partial_data"] == {"partial": "data"}
        assert partial["checkpoint_id"] == checkpoint.checkpoint_id
        assert partial["actions_completed"] == 2  # checkpoint + search action

    # -------------------------------------------------------------------------
    # User Confirmation Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_request_user_confirmation_autonomous(self) -> None:
        """Test that autonomous mode skips user confirmation."""
        agent = TestAgent(autonomy_mode=AutonomyMode.AUTONOMOUS)

        response = await agent.request_user_confirmation("Proceed with action?")

        assert response == "yes"

    @pytest.mark.asyncio
    async def test_request_user_confirmation_cautious(self) -> None:
        """Test user confirmation in cautious mode (returns default for now)."""
        agent = TestAgent(autonomy_mode=AutonomyMode.CAUTIOUS)

        response = await agent.request_user_confirmation("Proceed?", options=["yes", "no", "skip"])

        # Current implementation returns "yes" as default
        assert response == "yes"

    # -------------------------------------------------------------------------
    # Audit Log Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_audit_log_creation(self) -> None:
        """Test that audit log is properly created."""
        case_context = CaseContext(
            case_id="AUDIT-TEST-001",
            title="Audit Test Case",
            case_type="litigation",
        )

        agent = TestAgent(
            case_context=case_context,
            user_id="auditor",
            firm_id="audit-firm",
        )

        result = await agent.execute("Generate audit log")

        audit_log = result.audit_log

        assert audit_log.case_id == "AUDIT-TEST-001"
        assert audit_log.user_id == "auditor"
        assert audit_log.firm_id == "audit-firm"
        assert audit_log.agent_id == "test-agent"
        assert audit_log.agent_version == "1.0.0"
        assert audit_log.autonomy_mode == AutonomyMode.BALANCED
        assert audit_log.outcome == AgentOutcome.SUCCESS
        assert len(audit_log.actions) >= 1

    # -------------------------------------------------------------------------
    # Sub-Agent Invocation Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_invoke_sub_agent(self) -> None:
        """Test invoking a sub-agent."""
        case_context = CaseContext(
            case_id="SUB-AGENT-TEST",
            title="Sub-Agent Test",
            case_type="contract",
        )

        parent_agent = TestAgent(
            case_context=case_context,
            user_id="parent-user",
            firm_id="parent-firm",
        )

        # Invoke sub-agent
        result = await parent_agent.invoke_sub_agent(
            TestAgent,
            "Sub-task",
        )

        assert result.success is True
        # Parent should have checkpoints
        assert len(parent_agent._checkpoints) >= 1
        # Parent should have recorded the sub-agent invocation
        invoke_actions = [
            a for a in parent_agent._actions if a.action_type == ActionType.INVOKE_AGENT
        ]
        assert len(invoke_actions) >= 1

    @pytest.mark.asyncio
    async def test_invoke_sub_agent_autonomy_override(self) -> None:
        """Test invoking a sub-agent with autonomy override."""
        parent_agent = TestAgent(autonomy_mode=AutonomyMode.AUTONOMOUS)

        # Invoke with cautious override
        # Note: We can't directly test the sub-agent's mode without modifying TestAgent,
        # but we can verify the invocation succeeds
        result = await parent_agent.invoke_sub_agent(
            TestAgent,
            "Careful task",
            autonomy_override=AutonomyMode.CAUTIOUS,
        )

        assert result.success is True
