"""
BetterCallClaude Agent Orchestrator

Multi-agent pipeline coordinator for complex legal workflows.
Chains Research → Strategy → Draft with data passing and checkpoint management.

Supports:
- Python agents: researcher, strategist, drafter (built-in)
- Command agents: All 11 command-based agents via CommandAgentAdapter

Pipelines:
- research_to_strategy: Research findings → Strategy recommendations
- strategy_to_draft: Strategy → Legal document drafting
- full_pipeline: Complete Research → Strategy → Draft chain
- custom_pipeline: Any combination of registered agents
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import (
    AgentBase,
    AgentResult,
    AutonomyMode,
    CaseContext,
    Checkpoint,
)
from .models.drafter import DocumentType
from .models.shared import (
    CaseFacts,
    Jurisdiction,
    Language,
    LegalParty,
)

if TYPE_CHECKING:
    from .registry import AgentRegistry

logger = logging.getLogger(__name__)


# =============================================================================
# Orchestration Data Classes
# =============================================================================


class PipelineStatus(Enum):
    """Status of pipeline execution."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_CHECKPOINT = "awaiting_checkpoint"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OrchestrationStep:
    """
    Definition of a single step in an orchestration pipeline.

    Attributes:
        agent_type: Type of agent to execute (researcher, strategist, drafter)
        task: Task description for the agent
        input_mapping: Dict mapping step inputs from previous outputs
        output_key: Key to store this step's output
        checkpoint_required: Whether to checkpoint before this step
        condition: Optional condition function for conditional execution
    """

    agent_type: str
    task: str
    input_mapping: dict[str, str] = field(default_factory=dict)
    output_key: str = ""
    checkpoint_required: bool = False
    condition: Callable[[dict[str, Any]], bool] | None = None

    def __post_init__(self) -> None:
        """Set default output key if not provided."""
        if not self.output_key:
            self.output_key = f"{self.agent_type}_output"


@dataclass
class PipelineResult:
    """
    Result of pipeline execution.

    Attributes:
        pipeline_id: Unique identifier for this execution
        status: Current status of the pipeline
        steps_completed: List of completed step names
        step_results: Results from each step
        aggregated_checkpoints: All checkpoints across agents
        total_duration_seconds: Total execution time
        final_output: The final aggregated output
        errors: Any errors encountered
    """

    pipeline_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: PipelineStatus = PipelineStatus.PENDING
    steps_completed: list[str] = field(default_factory=list)
    step_results: dict[str, AgentResult] = field(default_factory=dict)
    aggregated_checkpoints: list[Checkpoint] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    final_output: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PipelineConfig:
    """
    Configuration for pipeline execution.

    Attributes:
        autonomy_mode: Default autonomy mode for agents
        language: Default output language
        jurisdiction: Default jurisdiction
        fail_fast: Stop on first error
        aggregate_checkpoints: Collect checkpoints from all agents
        max_retries: Maximum retries per step
        timeout_seconds: Timeout for entire pipeline
    """

    autonomy_mode: AutonomyMode = AutonomyMode.CAUTIOUS
    language: Language = Language.DE
    jurisdiction: Jurisdiction = Jurisdiction.FEDERAL
    fail_fast: bool = True
    aggregate_checkpoints: bool = True
    max_retries: int = 2
    timeout_seconds: int = 600


# =============================================================================
# Pipeline Templates
# =============================================================================


PIPELINE_TEMPLATES = {
    "research_to_strategy": [
        OrchestrationStep(
            agent_type="researcher",
            task="Research legal precedents and relevant law",
            output_key="research_output",
            checkpoint_required=False,
        ),
        OrchestrationStep(
            agent_type="strategist",
            task="Develop litigation strategy based on research",
            input_mapping={"research_results": "research_output.findings"},
            output_key="strategy_output",
            checkpoint_required=True,
        ),
    ],
    "strategy_to_draft": [
        OrchestrationStep(
            agent_type="strategist",
            task="Finalize strategy recommendations",
            output_key="strategy_output",
            checkpoint_required=True,
        ),
        OrchestrationStep(
            agent_type="drafter",
            task="Draft legal document based on strategy",
            input_mapping={"strategy_input": "strategy_output.recommendation"},
            output_key="document_output",
            checkpoint_required=True,
        ),
    ],
    "full_pipeline": [
        OrchestrationStep(
            agent_type="researcher",
            task="Comprehensive legal research",
            output_key="research_output",
            checkpoint_required=False,
        ),
        OrchestrationStep(
            agent_type="strategist",
            task="Strategic analysis and recommendations",
            input_mapping={"research_results": "research_output.findings"},
            output_key="strategy_output",
            checkpoint_required=True,
        ),
        OrchestrationStep(
            agent_type="drafter",
            task="Document drafting",
            input_mapping={
                "strategy_input": "strategy_output.recommendation",
                "research_context": "research_output.findings",
            },
            output_key="document_output",
            checkpoint_required=True,
        ),
    ],
}


# =============================================================================
# Agent Orchestrator
# =============================================================================


class AgentOrchestrator:
    """
    Orchestrator for multi-agent legal workflows.

    Coordinates execution of Research → Strategy → Draft pipelines
    with data passing, checkpoint management, and error handling.

    Supports all 14 agents:
    - Python agents (built-in): researcher, strategist, drafter
    - Command agents (via adapter): analyzer, auditor, briefer, compliance, consultant,
      discovery, evaluator, mediator, negotiator, optimizer, reviewer

    Example usage:
        orchestrator = AgentOrchestrator(
            autonomy_mode=AutonomyMode.CAUTIOUS,
            case_context=case_context
        )

        # Full pipeline
        result = await orchestrator.full_pipeline(
            query="Analyze contract breach case",
            case_facts={"summary": "..."},
            document_type="klageschrift"
        )

        # Custom pipeline with any agents
        result = await orchestrator.execute_pipeline([
            OrchestrationStep(agent_type="researcher", task="..."),
            OrchestrationStep(agent_type="analyzer", task="..."),
            OrchestrationStep(agent_type="evaluator", task="..."),
        ])
    """

    # Orchestrator version
    VERSION = "2.0.0"

    # Legacy: Hardcoded Python agent types (for backward compatibility)
    _PYTHON_AGENT_TYPES = ["researcher", "strategist", "drafter"]

    def __init__(
        self,
        autonomy_mode: AutonomyMode = AutonomyMode.CAUTIOUS,
        case_context: CaseContext | None = None,
        config: PipelineConfig | None = None,
        commands_dir: Path | str | None = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            autonomy_mode: Default autonomy level for agents
            case_context: Shared case context across agents
            config: Pipeline configuration options
            commands_dir: Directory containing command files (for command-based agents)
        """
        self.autonomy_mode = autonomy_mode
        self.case_context = case_context
        self.config = config or PipelineConfig(autonomy_mode=autonomy_mode)
        self.step_results: dict[str, AgentResult] = {}
        self._agents: dict[str, AgentBase] = {}
        self._pipeline_history: list[PipelineResult] = []
        self._registry: AgentRegistry | None = None
        self._commands_dir = Path(commands_dir) if commands_dir else None

        logger.info(
            f"AgentOrchestrator initialized (mode={autonomy_mode.value}, "
            f"version={self.VERSION})"
        )

    # =========================================================================
    # Registry Integration (NEW)
    # =========================================================================

    @cached_property
    def registry(self) -> AgentRegistry:
        """
        Get or create the agent registry.

        Returns:
            AgentRegistry instance with all discovered agents
        """
        from .registry import AgentRegistry

        if self._registry is None:
            self._registry = AgentRegistry(commands_dir=self._commands_dir)
            logger.info(f"Registry initialized with {len(self._registry)} agents")
        return self._registry

    @property
    def AGENT_TYPES(self) -> list[str]:
        """
        Get list of all supported agent types (dynamic).

        Returns both Python and command-based agents.
        """
        # Get from registry if available
        try:
            return [desc.agent_id for desc in self.registry.list_agents()]
        except Exception:
            # Fall back to Python agents if registry fails
            return self._PYTHON_AGENT_TYPES.copy()

    def get_agent_info(self, agent_type: str) -> dict[str, Any]:
        """
        Get detailed information about an agent.

        Args:
            agent_type: Agent type identifier

        Returns:
            Dict with agent metadata
        """
        descriptor = self.registry.get_agent(agent_type)
        if descriptor:
            return {
                "agent_id": descriptor.agent_id,
                "name": descriptor.name,
                "version": descriptor.version,
                "description": descriptor.description,
                "agent_type": descriptor.agent_type,
                "category": descriptor.category.value,
                "is_python_agent": descriptor.agent_type == "python",
            }
        return {}

    # =========================================================================
    # Agent Management
    # =========================================================================

    def _get_agent(self, agent_type: str) -> AgentBase:
        """
        Get or create an agent instance.

        Supports both built-in Python agents and command-based agents via the registry.

        Args:
            agent_type: Type of agent (e.g., researcher, strategist, drafter, analyzer, etc.)

        Returns:
            AgentBase instance (Python agent or CommandAgentAdapter)

        Raises:
            ValueError: If agent type is unknown or not registered
        """
        if agent_type in self._agents:
            return self._agents[agent_type]

        agent: AgentBase

        # First, try built-in Python agents (fast path)
        if agent_type in self._PYTHON_AGENT_TYPES:
            agent = self._create_python_agent(agent_type)
        else:
            # Try to get from registry (command-based agents)
            agent = self._create_command_agent(agent_type)

        self._agents[agent_type] = agent
        return agent

    def _create_python_agent(self, agent_type: str) -> AgentBase:
        """
        Create a built-in Python agent instance.

        Args:
            agent_type: Type of Python agent (researcher, strategist, drafter)

        Returns:
            Python AgentBase instance
        """
        # Lazy import to avoid circular dependencies
        if agent_type == "researcher":
            from .researcher import ResearcherAgent

            return ResearcherAgent(
                autonomy_mode=self.autonomy_mode,
                case_context=self.case_context,
            )
        elif agent_type == "strategist":
            from .strategist import StrategistAgent

            return StrategistAgent(
                autonomy_mode=self.autonomy_mode,
                case_context=self.case_context,
            )
        elif agent_type == "drafter":
            from .drafter import DrafterAgent

            return DrafterAgent(
                autonomy_mode=self.autonomy_mode,
                case_context=self.case_context,
            )
        else:
            raise ValueError(f"Unknown Python agent type: {agent_type}")

    def _create_command_agent(self, agent_type: str) -> AgentBase:
        """
        Create a command-based agent via CommandAgentAdapter.

        Args:
            agent_type: Type of command agent (e.g., analyzer, evaluator, etc.)

        Returns:
            CommandAgentAdapter instance wrapping the command-based agent

        Raises:
            ValueError: If agent type is not found in registry
        """
        from .command_adapter import CommandAgentAdapter

        # Look up in registry
        descriptor = self.registry.get_agent(agent_type)
        if descriptor is None:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available agents: {', '.join(self.AGENT_TYPES)}"
            )

        # Check if it's actually a command-based agent
        if descriptor.agent_type != "command":
            raise ValueError(
                f"Agent '{agent_type}' is not a command-based agent "
                f"(type: {descriptor.agent_type})"
            )

        # Create adapter from descriptor
        logger.info(f"Creating CommandAgentAdapter for '{agent_type}'")
        return CommandAgentAdapter.from_descriptor(
            descriptor=descriptor,
            autonomy_mode=self.autonomy_mode,
            case_context=self.case_context,
        )

    # =========================================================================
    # Data Passing Utilities
    # =========================================================================

    def _resolve_input_mapping(
        self,
        mapping: dict[str, str],
        step_results: dict[str, AgentResult],
    ) -> dict[str, Any]:
        """
        Resolve input mapping from previous step outputs.

        Args:
            mapping: Dict of {input_name: "step_key.path.to.value"}
            step_results: Results from previous steps

        Returns:
            Dict with resolved values
        """
        resolved = {}

        for input_name, source_path in mapping.items():
            try:
                parts = source_path.split(".")
                step_key = parts[0]

                if step_key not in step_results:
                    logger.warning(f"Step '{step_key}' not found for mapping")
                    continue

                # Navigate the path
                current_value: Any = step_results[step_key]

                # Get the deliverable from AgentResult
                if hasattr(current_value, "deliverable"):
                    current_value = current_value.deliverable

                for part in parts[1:]:
                    if hasattr(current_value, part):
                        current_value = getattr(current_value, part)
                    elif isinstance(current_value, dict) and part in current_value:
                        current_value = current_value[part]
                    else:
                        logger.warning(f"Path '{part}' not found in {type(current_value)}")
                        current_value = None
                        break

                resolved[input_name] = current_value

            except Exception as e:
                logger.error(f"Error resolving mapping {input_name}: {e}")
                resolved[input_name] = None

        return resolved

    def _aggregate_checkpoints(
        self,
        step_results: dict[str, AgentResult],
    ) -> list[Checkpoint]:
        """
        Aggregate checkpoints from all completed steps.

        Args:
            step_results: Results from completed steps

        Returns:
            List of all checkpoints
        """
        checkpoints = []

        for step_key, result in step_results.items():
            if hasattr(result, "checkpoints") and result.checkpoints:
                for cp in result.checkpoints:
                    # Tag checkpoint with source step
                    if not hasattr(cp, "source_step"):
                        cp.source_step = step_key
                    checkpoints.append(cp)

        return checkpoints

    # =========================================================================
    # Pipeline Execution
    # =========================================================================

    async def execute_pipeline(
        self,
        steps: list[OrchestrationStep],
        initial_inputs: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """
        Execute a multi-agent pipeline with data passing.

        Args:
            steps: List of OrchestrationStep definitions
            initial_inputs: Initial inputs for the first step

        Returns:
            PipelineResult with all step outputs and aggregated checkpoints
        """
        result = PipelineResult(status=PipelineStatus.IN_PROGRESS)
        start_time = datetime.now()
        step_results: dict[str, AgentResult] = {}

        logger.info(f"Starting pipeline {result.pipeline_id} with {len(steps)} steps")

        try:
            for i, step in enumerate(steps):
                step_name = f"step_{i}_{step.agent_type}"
                logger.info(f"Executing {step_name}: {step.task}")

                # Check condition if present
                if step.condition and not step.condition(step_results):
                    logger.info(f"Skipping {step_name}: condition not met")
                    continue

                # Resolve inputs from previous steps
                resolved_inputs = {}
                if step.input_mapping:
                    resolved_inputs = self._resolve_input_mapping(step.input_mapping, step_results)

                # Merge with initial inputs for first step
                if i == 0 and initial_inputs:
                    resolved_inputs.update(initial_inputs)

                # Get agent and execute
                agent = self._get_agent(step.agent_type)

                try:
                    # Execute based on agent type
                    step_result = await self._execute_step(
                        agent=agent,
                        step=step,
                        inputs=resolved_inputs,
                    )

                    step_results[step.output_key] = step_result
                    result.steps_completed.append(step.output_key)

                    # Check for checkpoint requirement
                    if (
                        step.checkpoint_required
                        and hasattr(step_result, "checkpoints")
                        and step_result.checkpoints
                    ):
                        result.status = PipelineStatus.AWAITING_CHECKPOINT
                        logger.info(f"Pipeline paused at {step_name} for checkpoint")

                except Exception as e:
                    error_msg = f"Step {step_name} failed: {str(e)}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)

                    if self.config.fail_fast:
                        result.status = PipelineStatus.FAILED
                        break

            # Finalize result
            if result.status == PipelineStatus.IN_PROGRESS:
                result.status = PipelineStatus.COMPLETED

            result.step_results = step_results
            result.aggregated_checkpoints = self._aggregate_checkpoints(step_results)
            result.total_duration_seconds = (datetime.now() - start_time).total_seconds()

            # Create final output summary
            result.final_output = self._create_final_output(step_results)

        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.errors.append(f"Pipeline error: {str(e)}")
            logger.error(f"Pipeline {result.pipeline_id} failed: {e}")

        # Store in history
        self._pipeline_history.append(result)
        self.step_results = step_results

        logger.info(
            f"Pipeline {result.pipeline_id} {result.status.value} "
            f"in {result.total_duration_seconds:.2f}s"
        )

        return result

    async def _execute_step(
        self,
        agent: AgentBase,
        step: OrchestrationStep,
        inputs: dict[str, Any],
    ) -> AgentResult:
        """
        Execute a single pipeline step.

        Supports both Python agents (researcher, strategist, drafter) and
        command-based agents (via CommandAgentAdapter).

        Args:
            agent: Agent instance to execute
            step: Step definition
            inputs: Resolved inputs for the step

        Returns:
            AgentResult from the step execution
        """
        # Build execution kwargs based on agent type
        if step.agent_type == "researcher":
            return await agent.execute(
                task=step.task,
                query=inputs.get("query", step.task),
                **{k: v for k, v in inputs.items() if k not in ["query"]},
            )
        elif step.agent_type == "strategist":
            case_facts = inputs.get("case_facts")
            if isinstance(case_facts, dict):
                case_facts = CaseFacts(**case_facts) if case_facts else None

            return await agent.execute(
                task=step.task,
                case_facts=case_facts,
                jurisdiction=inputs.get("jurisdiction", self.config.jurisdiction),
                language=inputs.get("language", self.config.language),
                **{
                    k: v
                    for k, v in inputs.items()
                    if k not in ["case_facts", "jurisdiction", "language"]
                },
            )
        elif step.agent_type == "drafter":
            return await agent.execute(
                task=step.task,
                document_type=inputs.get("document_type", DocumentType.MEMORANDUM),
                language=inputs.get("language", self.config.language),
                jurisdiction=inputs.get("jurisdiction", self.config.jurisdiction),
                case_facts=inputs.get("case_facts"),
                strategy_input=inputs.get("strategy_input"),
                **{
                    k: v
                    for k, v in inputs.items()
                    if k
                    not in [
                        "document_type",
                        "language",
                        "jurisdiction",
                        "case_facts",
                        "strategy_input",
                    ]
                },
            )
        else:
            # Command-based agents - use generic execution interface
            return await self._execute_command_agent_step(agent, step, inputs)

    async def _execute_command_agent_step(
        self,
        agent: AgentBase,
        step: OrchestrationStep,
        inputs: dict[str, Any],
    ) -> AgentResult:
        """
        Execute a step using a command-based agent.

        Command-based agents have a simpler interface: they receive the task
        and all inputs as keyword arguments.

        Args:
            agent: CommandAgentAdapter instance
            step: Step definition
            inputs: Resolved inputs for the step

        Returns:
            AgentResult from command execution
        """
        # Prepare execution kwargs with common parameters
        exec_kwargs: dict[str, Any] = {
            "task": step.task,
            "language": inputs.get("language", self.config.language),
            "jurisdiction": inputs.get("jurisdiction", self.config.jurisdiction),
        }

        # Add any additional inputs from previous steps
        for key, value in inputs.items():
            if key not in exec_kwargs:
                exec_kwargs[key] = value

        logger.debug(
            f"Executing command agent '{step.agent_type}' with keys: {list(exec_kwargs.keys())}"
        )

        return await agent.execute(**exec_kwargs)

    def _create_final_output(
        self,
        step_results: dict[str, AgentResult],
    ) -> dict[str, Any]:
        """
        Create aggregated final output from all steps.

        Args:
            step_results: Results from all steps

        Returns:
            Dict with summarized output
        """
        output: dict[str, Any] = {
            "summary": {},
            "deliverables": {},
            "metrics": {},
        }

        for key, result in step_results.items():
            # Extract deliverable
            if hasattr(result, "deliverable") and result.deliverable:
                deliverable = result.deliverable
                if hasattr(deliverable, "to_dict"):
                    output["deliverables"][key] = deliverable.to_dict()
                else:
                    output["deliverables"][key] = str(deliverable)

            # Extract metrics
            if hasattr(result, "metadata") and result.metadata:
                output["metrics"][key] = result.metadata

            # Create summary
            if hasattr(result, "outcome"):
                output["summary"][key] = result.outcome.value

        return output

    # =========================================================================
    # Convenience Pipeline Methods
    # =========================================================================

    async def research_to_strategy(
        self,
        research_query: str,
        case_facts: dict | CaseFacts,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        language: Language = Language.DE,
    ) -> PipelineResult:
        """
        Execute Research → Strategy pipeline.

        Args:
            research_query: Query for legal research
            case_facts: Facts of the case
            jurisdiction: Legal jurisdiction
            language: Output language

        Returns:
            PipelineResult with research and strategy outputs
        """
        logger.info("Starting research_to_strategy pipeline")

        steps = [
            OrchestrationStep(
                agent_type="researcher",
                task=research_query,
                output_key="research_output",
                checkpoint_required=False,
            ),
            OrchestrationStep(
                agent_type="strategist",
                task="Develop litigation strategy based on research findings",
                input_mapping={
                    "research_results": "research_output",
                },
                output_key="strategy_output",
                checkpoint_required=True,
            ),
        ]

        initial_inputs = {
            "query": research_query,
            "case_facts": case_facts,
            "jurisdiction": jurisdiction,
            "language": language,
        }

        return await self.execute_pipeline(steps, initial_inputs)

    async def strategy_to_draft(
        self,
        strategy: dict | Any,
        document_type: str | DocumentType,
        case_facts: dict | CaseFacts | None = None,
        parties: list[LegalParty] | None = None,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        language: Language = Language.DE,
    ) -> PipelineResult:
        """
        Execute Strategy → Draft pipeline.

        Args:
            strategy: Strategy recommendation or dict
            document_type: Type of document to draft
            case_facts: Optional case facts
            parties: Optional list of parties
            jurisdiction: Legal jurisdiction
            language: Document language

        Returns:
            PipelineResult with draft output
        """
        logger.info("Starting strategy_to_draft pipeline")

        # Normalize document type
        if isinstance(document_type, str):
            document_type = DocumentType(document_type.lower())

        steps = [
            OrchestrationStep(
                agent_type="drafter",
                task=f"Draft {document_type.value} based on strategic recommendations",
                output_key="document_output",
                checkpoint_required=True,
            ),
        ]

        initial_inputs = {
            "strategy_input": strategy,
            "document_type": document_type,
            "case_facts": case_facts,
            "parties": parties,
            "jurisdiction": jurisdiction,
            "language": language,
        }

        return await self.execute_pipeline(steps, initial_inputs)

    async def full_pipeline(
        self,
        query: str,
        case_facts: dict | CaseFacts,
        document_type: str | DocumentType,
        parties: list[LegalParty] | None = None,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        language: Language = Language.DE,
    ) -> PipelineResult:
        """
        Execute full Research → Strategy → Draft pipeline.

        Args:
            query: Research query
            case_facts: Facts of the case
            document_type: Type of document to produce
            parties: Optional list of parties
            jurisdiction: Legal jurisdiction
            language: Output language

        Returns:
            PipelineResult with all outputs
        """
        logger.info("Starting full_pipeline: Research → Strategy → Draft")

        # Normalize document type
        if isinstance(document_type, str):
            document_type = DocumentType(document_type.lower())

        steps = [
            OrchestrationStep(
                agent_type="researcher",
                task=query,
                output_key="research_output",
                checkpoint_required=False,
            ),
            OrchestrationStep(
                agent_type="strategist",
                task="Develop comprehensive litigation strategy",
                input_mapping={
                    "research_results": "research_output",
                },
                output_key="strategy_output",
                checkpoint_required=True,
            ),
            OrchestrationStep(
                agent_type="drafter",
                task=f"Draft {document_type.value}",
                input_mapping={
                    "strategy_input": "strategy_output",
                    "research_context": "research_output",
                },
                output_key="document_output",
                checkpoint_required=True,
            ),
        ]

        initial_inputs = {
            "query": query,
            "case_facts": case_facts,
            "document_type": document_type,
            "parties": parties,
            "jurisdiction": jurisdiction,
            "language": language,
        }

        return await self.execute_pipeline(steps, initial_inputs)

    # =========================================================================
    # Pipeline Management
    # =========================================================================

    def get_pipeline_history(self) -> list[PipelineResult]:
        """Get history of executed pipelines."""
        return self._pipeline_history.copy()

    def get_latest_result(self) -> PipelineResult | None:
        """Get the most recent pipeline result."""
        return self._pipeline_history[-1] if self._pipeline_history else None

    def clear_history(self) -> None:
        """Clear pipeline history."""
        self._pipeline_history.clear()
        self.step_results.clear()
        logger.info("Pipeline history cleared")

    # =========================================================================
    # Checkpoint Management
    # =========================================================================

    async def resume_from_checkpoint(
        self,
        pipeline_id: str,
        checkpoint_response: dict[str, Any],
    ) -> PipelineResult:
        """
        Resume a paused pipeline after checkpoint approval.

        Args:
            pipeline_id: ID of the paused pipeline
            checkpoint_response: User response to checkpoint

        Returns:
            Updated PipelineResult
        """
        # Find the paused pipeline
        paused = None
        for result in self._pipeline_history:
            if result.pipeline_id == pipeline_id:
                paused = result
                break

        if not paused:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        if paused.status != PipelineStatus.AWAITING_CHECKPOINT:
            raise ValueError(f"Pipeline {pipeline_id} is not awaiting checkpoint")

        logger.info(f"Resuming pipeline {pipeline_id} from checkpoint")

        # Update status and continue
        # (In a full implementation, this would resume from the last step)
        paused.status = PipelineStatus.COMPLETED
        return paused

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_supported_pipelines(self) -> list[str]:
        """Get list of supported pipeline templates."""
        return list(PIPELINE_TEMPLATES.keys())

    def get_pipeline_template(self, name: str) -> list[OrchestrationStep]:
        """Get a pipeline template by name."""
        if name not in PIPELINE_TEMPLATES:
            raise ValueError(f"Unknown pipeline: {name}")
        return PIPELINE_TEMPLATES[name].copy()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AgentOrchestrator("
            f"mode={self.autonomy_mode.value}, "
            f"pipelines_run={len(self._pipeline_history)}, "
            f"version={self.VERSION})"
        )
