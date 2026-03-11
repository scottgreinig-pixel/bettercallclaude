"""
BetterCallClaude Agent Base Class

This module provides the foundational classes for building legal intelligence agents.
All agents inherit from AgentBase and implement the execute() method.

Architecture:
- AgentBase: Core functionality (checkpoints, audit, sub-agent invocation)
- AutonomyMode: Enum for cautious/balanced/autonomous modes
- CaseContext: Shared context across agent executions
- AgentResult: Standardized result format
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar, cast

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Types
# =============================================================================


class AutonomyMode(Enum):
    """
    Autonomy levels controlling agent interaction with user.

    CAUTIOUS: Confirms before each significant action
    BALANCED: Confirms at key checkpoints only (default)
    AUTONOMOUS: Runs to completion with minimal interruption
    """

    CAUTIOUS = "cautious"
    BALANCED = "balanced"
    AUTONOMOUS = "autonomous"


class AgentOutcome(Enum):
    """Result status of agent execution."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(Enum):
    """Types of actions an agent can perform."""

    SEARCH = "search"
    ANALYZE = "analyze"
    GENERATE = "generate"
    INVOKE_AGENT = "invoke_agent"
    CHECKPOINT = "checkpoint"
    USER_CONFIRM = "user_confirm"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Party:
    """Represents a party in a legal case."""

    name: str
    role: str  # e.g., "client", "plaintiff", "defendant"
    contact: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseContext:
    """
    Shared context for a legal case, inherited by all agents.

    This context persists across agent executions and enables
    agents to build on each other's findings.
    """

    case_id: str
    title: str
    case_type: str  # litigation, corporate, contract, regulatory, other
    jurisdiction_federal: bool = True
    jurisdiction_cantons: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=lambda: ["DE"])
    parties: list[Party] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    legal_issues: list[str] = field(default_factory=list)
    agent_history: list[str] = field(default_factory=list)
    findings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Serialize case context to dictionary."""
        return {
            "case_id": self.case_id,
            "title": self.title,
            "case_type": self.case_type,
            "jurisdiction": {
                "federal": self.jurisdiction_federal,
                "cantons": self.jurisdiction_cantons,
                "languages": self.languages,
            },
            "parties": [
                {"name": p.name, "role": p.role, "metadata": p.metadata} for p in self.parties
            ],
            "facts": self.facts,
            "legal_issues": self.legal_issues,
            "agent_history": self.agent_history,
            "findings": self.findings,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AgentAction:
    """Records a single action taken by an agent."""

    action_id: str
    timestamp: datetime
    action_type: ActionType
    description: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    duration_ms: int
    sub_agent_id: str | None = None

    @classmethod
    def create(
        cls,
        action_type: ActionType,
        description: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        duration_ms: int,
        sub_agent_id: str | None = None,
    ) -> "AgentAction":
        """Factory method to create an action with auto-generated ID and timestamp."""
        return cls(
            action_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            action_type=action_type,
            description=description,
            inputs=inputs,
            outputs=outputs,
            duration_ms=duration_ms,
            sub_agent_id=sub_agent_id,
        )


@dataclass
class Checkpoint:
    """Snapshot of agent state for recovery."""

    checkpoint_id: str
    timestamp: datetime
    checkpoint_type: str  # auto, user, pre_external, pre_subagent
    state: dict[str, Any]
    description: str

    @classmethod
    def create(cls, checkpoint_type: str, state: dict[str, Any], description: str) -> "Checkpoint":
        """Factory method to create a checkpoint."""
        return cls(
            checkpoint_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            checkpoint_type=checkpoint_type,
            state=state,
            description=description,
        )


@dataclass
class AgentAuditLog:
    """Complete audit trail for an agent execution."""

    log_id: str
    timestamp: datetime
    case_id: str
    user_id: str
    firm_id: str
    agent_id: str
    agent_version: str
    autonomy_mode: AutonomyMode
    actions: list[AgentAction]
    sources_accessed: list[str]
    documents_read: list[str]
    documents_written: list[str]
    outcome: AgentOutcome
    deliverables: list[str]
    errors: list[dict[str, Any]]
    checkpoints: list[Checkpoint]

    def to_dict(self) -> dict[str, Any]:
        """Serialize audit log to dictionary for storage."""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "case_id": self.case_id,
            "user_id": self.user_id,
            "firm_id": self.firm_id,
            "agent_id": self.agent_id,
            "agent_version": self.agent_version,
            "autonomy_mode": self.autonomy_mode.value,
            "actions": [
                {
                    "action_id": a.action_id,
                    "timestamp": a.timestamp.isoformat(),
                    "type": a.action_type.value,
                    "description": a.description,
                    "duration_ms": a.duration_ms,
                }
                for a in self.actions
            ],
            "sources_accessed": self.sources_accessed,
            "documents_read": self.documents_read,
            "documents_written": self.documents_written,
            "outcome": self.outcome.value,
            "deliverables": self.deliverables,
            "errors": self.errors,
            "checkpoints": [
                {
                    "checkpoint_id": c.checkpoint_id,
                    "timestamp": c.timestamp.isoformat(),
                    "type": c.checkpoint_type,
                    "description": c.description,
                }
                for c in self.checkpoints
            ],
        }


T = TypeVar("T")


@dataclass
class AgentResult(Generic[T]):
    """
    Standardized result format for agent execution.

    Type parameter T represents the specific deliverable type.
    """

    success: bool
    outcome: AgentOutcome
    deliverable: T | None
    partial_results: T | None
    error_message: str | None
    audit_log: AgentAuditLog
    execution_time_ms: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "success": self.success,
            "outcome": self.outcome.value,
            "deliverable": self.deliverable,
            "partial_results": self.partial_results,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "audit_log_id": self.audit_log.log_id,
        }


# =============================================================================
# Agent Base Class
# =============================================================================


class AgentBase(ABC):
    """
    Abstract base class for all BetterCallClaude agents.

    Provides core functionality:
    - Autonomy mode management
    - Checkpoint creation and recovery
    - Audit logging
    - Sub-agent invocation
    - Case context handling

    Subclasses must implement:
    - execute(): Main agent logic
    - agent_id: Unique identifier
    - agent_version: Version string
    """

    def __init__(
        self,
        autonomy_mode: AutonomyMode = AutonomyMode.BALANCED,
        case_context: CaseContext | None = None,
        user_id: str = "anonymous",
        firm_id: str = "default",
    ):
        """
        Initialize agent with configuration.

        Args:
            autonomy_mode: Level of autonomous operation
            case_context: Shared case context (optional)
            user_id: Identifier for the executing user
            firm_id: Identifier for the firm
        """
        self.autonomy_mode = autonomy_mode
        self.case_context = case_context
        self.user_id = user_id
        self.firm_id = firm_id

        # Execution state
        self._actions: list[AgentAction] = []
        self._checkpoints: list[Checkpoint] = []
        self._sources_accessed: list[str] = []
        self._documents_read: list[str] = []
        self._documents_written: list[str] = []
        self._errors: list[dict[str, Any]] = []
        self._start_time: datetime | None = None
        self._current_state: dict[str, Any] = {}

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique identifier for this agent type (e.g., 'researcher')."""
        pass

    @property
    @abstractmethod
    def agent_version(self) -> str:
        """Version string for this agent (e.g., '1.0.0')."""
        pass

    @abstractmethod
    async def execute(self, task: str, **kwargs: Any) -> AgentResult[Any]:
        """
        Execute the agent's main task.

        Args:
            task: Description of the task to perform
            **kwargs: Additional task-specific parameters

        Returns:
            AgentResult with deliverable and audit information
        """
        pass

    # -------------------------------------------------------------------------
    # Checkpoint Management
    # -------------------------------------------------------------------------

    def create_checkpoint(self, checkpoint_type: str = "auto", description: str = "") -> Checkpoint:
        """
        Create a checkpoint of current state.

        Args:
            checkpoint_type: One of 'auto', 'user', 'pre_external', 'pre_subagent'
            description: Human-readable description of the checkpoint

        Returns:
            The created Checkpoint object
        """
        checkpoint = Checkpoint.create(
            checkpoint_type=checkpoint_type,
            state=self._current_state.copy(),
            description=description or f"Checkpoint at {datetime.utcnow().isoformat()}",
        )
        self._checkpoints.append(checkpoint)

        # Log checkpoint action
        self._record_action(
            ActionType.CHECKPOINT,
            f"Created {checkpoint_type} checkpoint",
            inputs={},
            outputs={"checkpoint_id": checkpoint.checkpoint_id},
            duration_ms=0,
        )

        logger.info(f"Checkpoint created: {checkpoint.checkpoint_id}")
        return checkpoint

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore state from a checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint to restore

        Returns:
            True if restoration successful, False otherwise
        """
        for cp in reversed(self._checkpoints):
            if cp.checkpoint_id == checkpoint_id:
                self._current_state = cp.state.copy()
                logger.info(f"Restored checkpoint: {checkpoint_id}")
                return True

        logger.warning(f"Checkpoint not found: {checkpoint_id}")
        return False

    def get_latest_checkpoint(self) -> Checkpoint | None:
        """Get the most recent checkpoint."""
        return self._checkpoints[-1] if self._checkpoints else None

    # -------------------------------------------------------------------------
    # Action Recording
    # -------------------------------------------------------------------------

    def _record_action(
        self,
        action_type: ActionType,
        description: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        duration_ms: int,
        sub_agent_id: str | None = None,
    ) -> AgentAction:
        """Record an action in the audit log."""
        action = AgentAction.create(
            action_type=action_type,
            description=description,
            inputs=self._sanitize_inputs(inputs),
            outputs=self._summarize_outputs(outputs),
            duration_ms=duration_ms,
            sub_agent_id=sub_agent_id,
        )
        self._actions.append(action)
        return action

    def _sanitize_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize inputs for audit logging.

        Removes sensitive data and truncates large values.
        """
        sanitized = {}
        sensitive_keys = {"password", "token", "secret", "key", "credential"}

        for key, value in inputs.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...[truncated]"
            else:
                sanitized[key] = value

        return sanitized

    def _summarize_outputs(self, outputs: dict[str, Any]) -> dict[str, Any]:
        """
        Summarize outputs for audit logging.

        Creates compact representation of large outputs.
        """
        summarized = {}

        for key, value in outputs.items():
            if isinstance(value, list):
                summarized[key] = f"[List with {len(value)} items]"
            elif isinstance(value, dict):
                summarized[key] = f"[Dict with {len(value)} keys]"
            elif isinstance(value, str) and len(value) > 500:
                summarized[key] = value[:500] + "...[truncated]"
            else:
                summarized[key] = value

        return summarized

    # -------------------------------------------------------------------------
    # Sub-Agent Invocation
    # -------------------------------------------------------------------------

    async def invoke_sub_agent(
        self,
        agent_class: type,
        task: str,
        autonomy_override: AutonomyMode | None = None,
        **kwargs: Any,
    ) -> AgentResult[Any]:
        """
        Invoke a sub-agent with context inheritance.

        Args:
            agent_class: The agent class to instantiate
            task: Task description for the sub-agent
            autonomy_override: Optional autonomy mode override
            **kwargs: Additional parameters for the sub-agent

        Returns:
            AgentResult from the sub-agent
        """
        # Create checkpoint before sub-agent invocation
        self.create_checkpoint("pre_subagent", f"Before invoking {agent_class.__name__}")

        # Inherit autonomy mode unless overridden
        sub_autonomy = autonomy_override or self.autonomy_mode

        # Instantiate sub-agent with inherited context
        sub_agent = agent_class(
            autonomy_mode=sub_autonomy,
            case_context=self.case_context,
            user_id=self.user_id,
            firm_id=self.firm_id,
        )

        start = datetime.utcnow()
        result = await sub_agent.execute(task, **kwargs)
        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        # Record the sub-agent invocation
        self._record_action(
            ActionType.INVOKE_AGENT,
            f"Invoked {sub_agent.agent_id}",
            inputs={"task": task, **kwargs},
            outputs={"outcome": result.outcome.value},
            duration_ms=duration_ms,
            sub_agent_id=sub_agent.agent_id,
        )

        return cast(AgentResult[Any], result)

    # -------------------------------------------------------------------------
    # User Interaction
    # -------------------------------------------------------------------------

    async def request_user_confirmation(
        self, message: str, options: list[str] | None = None
    ) -> str:
        """
        Request confirmation from user based on autonomy mode.

        In CAUTIOUS mode: Always requests
        In BALANCED mode: Requests at checkpoints
        In AUTONOMOUS mode: Skips (returns default)

        Args:
            message: Message to show user
            options: List of valid options (default: ["yes", "no"])

        Returns:
            User's response or "yes" in autonomous mode
        """
        if self.autonomy_mode == AutonomyMode.AUTONOMOUS:
            return "yes"

        # In real implementation, this would interact with the user
        # For now, we log and return default
        logger.info(f"User confirmation requested: {message}")

        self._record_action(
            ActionType.USER_CONFIRM,
            f"Requested user confirmation: {message}",
            inputs={"message": message, "options": options or ["yes", "no"]},
            outputs={"response": "yes"},
            duration_ms=0,
        )

        return "yes"

    # -------------------------------------------------------------------------
    # Audit Log Generation
    # -------------------------------------------------------------------------

    def _create_audit_log(self, outcome: AgentOutcome, deliverables: list[str]) -> AgentAuditLog:
        """Generate complete audit log for the execution."""
        return AgentAuditLog(
            log_id=str(uuid.uuid4()),
            timestamp=self._start_time or datetime.utcnow(),
            case_id=self.case_context.case_id if self.case_context else "no_case",
            user_id=self.user_id,
            firm_id=self.firm_id,
            agent_id=self.agent_id,
            agent_version=self.agent_version,
            autonomy_mode=self.autonomy_mode,
            actions=self._actions,
            sources_accessed=self._sources_accessed,
            documents_read=self._documents_read,
            documents_written=self._documents_written,
            outcome=outcome,
            deliverables=deliverables,
            errors=self._errors,
            checkpoints=self._checkpoints,
        )

    # -------------------------------------------------------------------------
    # Error Handling
    # -------------------------------------------------------------------------

    def _handle_error(self, error: Exception, recoverable: bool = True) -> None:
        """
        Handle an error during execution.

        Args:
            error: The exception that occurred
            recoverable: Whether execution can continue
        """
        error_record = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "recoverable": recoverable,
        }
        self._errors.append(error_record)
        logger.error(f"Agent error: {error}", exc_info=True)

        if recoverable:
            # Escalate to cautious mode
            self.autonomy_mode = AutonomyMode.CAUTIOUS
            logger.info("Escalated to cautious mode after error")

    def _create_partial_result(self, partial_data: Any) -> dict[str, Any]:
        """Create a partial result package when execution fails midway."""
        latest_checkpoint = self.get_latest_checkpoint()
        return {
            "partial_data": partial_data,
            "checkpoint_id": latest_checkpoint.checkpoint_id if latest_checkpoint else None,
            "actions_completed": len(self._actions),
            "recovered_at": datetime.utcnow().isoformat(),
        }

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def record_source_access(self, source: str) -> None:
        """Record access to an external source (for audit)."""
        self._sources_accessed.append(source)

    def record_document_read(self, document: str) -> None:
        """Record reading a document (for audit)."""
        self._documents_read.append(document)

    def record_document_write(self, document: str) -> None:
        """Record writing a document (for audit)."""
        self._documents_written.append(document)

    def update_state(self, key: str, value: Any) -> None:
        """Update internal state (included in checkpoints)."""
        self._current_state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get value from internal state."""
        return self._current_state.get(key, default)
