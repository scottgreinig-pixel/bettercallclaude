"""
BetterCallClaude Pipeline Builder

Fluent API for constructing multi-agent pipelines programmatically.
Supports sequential, parallel, and conditional execution patterns.

Example usage:
    builder = PipelineBuilder()

    # Sequential pipeline
    pipeline = (
        builder
        .add_step("researcher", "Research contract law")
        .add_step("strategist", "Develop strategy")
        .add_step("drafter", "Draft complaint")
        .build()
    )

    # Parallel pipeline
    pipeline = (
        builder
        .add_parallel_group([
            PipelineStep("researcher", "Research precedents"),
            PipelineStep("analyzer", "Analyze contract"),
        ])
        .add_step("strategist", "Synthesize findings")
        .build()
    )

    # Conditional pipeline
    pipeline = (
        builder
        .add_step("researcher", "Initial research")
        .add_conditional_step(
            condition=lambda ctx: ctx.get("needs_deep_analysis", False),
            step=PipelineStep("analyzer", "Deep analysis"),
        )
        .add_step("drafter", "Final document")
        .build()
    )
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from .base import AgentResult
from .models.shared import Jurisdiction, Language

if TYPE_CHECKING:
    from .orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


# =============================================================================
# Pipeline Step Definitions
# =============================================================================


class StepType(Enum):
    """Type of pipeline step."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ROUTER = "router"


@dataclass
class PipelineStep:
    """
    Definition of a single pipeline step.

    Attributes:
        agent_type: Type of agent to execute
        task: Task description for the agent
        step_id: Unique identifier for this step
        input_mapping: Dict mapping step inputs from previous outputs
        output_key: Key to store this step's output
        checkpoint_required: Whether to checkpoint before this step
        timeout_seconds: Timeout for this specific step
        retry_count: Number of retries for this step
    """

    agent_type: str
    task: str
    step_id: str = ""
    input_mapping: dict[str, str] = field(default_factory=dict)
    output_key: str = ""
    checkpoint_required: bool = False
    timeout_seconds: int | None = None
    retry_count: int = 0

    def __post_init__(self) -> None:
        """Set default values if not provided."""
        if not self.step_id:
            self.step_id = f"{self.agent_type}_{uuid.uuid4().hex[:6]}"
        if not self.output_key:
            self.output_key = f"{self.agent_type}_output"


@dataclass
class ParallelGroup:
    """
    A group of steps to execute in parallel.

    Attributes:
        steps: List of steps to execute concurrently
        group_id: Unique identifier for this group
        merge_strategy: How to combine outputs ('all', 'first_success', 'majority')
        timeout_seconds: Timeout for the entire group
    """

    steps: list[PipelineStep]
    group_id: str = ""
    merge_strategy: str = "all"
    timeout_seconds: int | None = None

    def __post_init__(self) -> None:
        """Set default group ID."""
        if not self.group_id:
            self.group_id = f"parallel_{uuid.uuid4().hex[:6]}"


@dataclass
class ConditionalStep:
    """
    A step that executes conditionally based on context.

    Attributes:
        condition: Callable that receives context and returns bool
        step: Step to execute if condition is True
        else_step: Optional step to execute if condition is False
        condition_name: Human-readable name for the condition
    """

    condition: Callable[[dict[str, Any]], bool]
    step: PipelineStep
    else_step: PipelineStep | None = None
    condition_name: str = ""


@dataclass
class RouterStep:
    """
    A step that routes to different agents based on context.

    Attributes:
        router_fn: Function that returns agent_type based on context
        task: Task description (same for all routes)
        routes: Dict mapping route keys to PipelineStep configurations
        default_route: Default route if router returns unknown key
    """

    router_fn: Callable[[dict[str, Any]], str]
    task: str
    routes: dict[str, PipelineStep] = field(default_factory=dict)
    default_route: str | None = None


# =============================================================================
# Pipeline Definition
# =============================================================================


@dataclass
class Pipeline:
    """
    Complete pipeline definition ready for execution.

    Attributes:
        pipeline_id: Unique identifier
        name: Human-readable pipeline name
        description: Pipeline description
        steps: Ordered list of execution items (steps, groups, conditionals)
        config: Pipeline configuration
        created_at: Creation timestamp
    """

    pipeline_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    description: str = ""
    steps: list[PipelineStep | ParallelGroup | ConditionalStep | RouterStep] = field(
        default_factory=list
    )
    initial_inputs: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __len__(self) -> int:
        """Return number of top-level steps."""
        return len(self.steps)


@dataclass
class PipelineExecutionResult:
    """
    Result of pipeline execution.

    Attributes:
        pipeline_id: ID of the executed pipeline
        status: Execution status
        step_results: Results from each step
        parallel_results: Results from parallel groups
        total_duration_seconds: Total execution time
        errors: Any errors encountered
    """

    pipeline_id: str
    status: str = "pending"
    step_results: dict[str, AgentResult] = field(default_factory=dict)
    parallel_results: dict[str, list[AgentResult]] = field(default_factory=dict)
    total_duration_seconds: float = 0.0
    final_output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# Pipeline Builder
# =============================================================================


class PipelineBuilder:
    """
    Fluent builder for constructing pipelines.

    Example:
        pipeline = (
            PipelineBuilder("case_analysis")
            .add_step("researcher", "Research precedents")
            .with_input_mapping({"query": "initial_query"})
            .add_step("strategist", "Develop strategy")
            .with_checkpoint()
            .add_step("drafter", "Draft document")
            .build()
        )
    """

    def __init__(
        self,
        name: str = "",
        description: str = "",
    ):
        """
        Initialize the pipeline builder.

        Args:
            name: Human-readable pipeline name
            description: Pipeline description
        """
        self._name = name
        self._description = description
        self._steps: list[PipelineStep | ParallelGroup | ConditionalStep | RouterStep] = []
        self._last_step: PipelineStep | None = None
        self._initial_inputs: dict[str, Any] = {}

    def add_step(
        self,
        agent_type: str,
        task: str,
        output_key: str = "",
    ) -> PipelineBuilder:
        """
        Add a sequential step to the pipeline.

        Args:
            agent_type: Type of agent to use
            task: Task description
            output_key: Key for storing output

        Returns:
            Self for chaining
        """
        step = PipelineStep(
            agent_type=agent_type,
            task=task,
            output_key=output_key,
        )
        self._steps.append(step)
        self._last_step = step
        return self

    def with_input_mapping(self, mapping: dict[str, str]) -> PipelineBuilder:
        """
        Add input mapping to the last added step.

        Args:
            mapping: Dict mapping input names to source paths

        Returns:
            Self for chaining
        """
        if self._last_step is None:
            raise ValueError("No step to add input mapping to")
        self._last_step.input_mapping = mapping
        return self

    def with_checkpoint(self) -> PipelineBuilder:
        """
        Mark the last step as requiring a checkpoint.

        Returns:
            Self for chaining
        """
        if self._last_step is None:
            raise ValueError("No step to add checkpoint to")
        self._last_step.checkpoint_required = True
        return self

    def with_timeout(self, seconds: int) -> PipelineBuilder:
        """
        Set timeout for the last added step.

        Args:
            seconds: Timeout in seconds

        Returns:
            Self for chaining
        """
        if self._last_step is None:
            raise ValueError("No step to add timeout to")
        self._last_step.timeout_seconds = seconds
        return self

    def with_retry(self, count: int) -> PipelineBuilder:
        """
        Set retry count for the last added step.

        Args:
            count: Number of retries

        Returns:
            Self for chaining
        """
        if self._last_step is None:
            raise ValueError("No step to add retry to")
        self._last_step.retry_count = count
        return self

    def add_parallel_group(
        self,
        steps: list[PipelineStep],
        merge_strategy: str = "all",
        timeout_seconds: int | None = None,
    ) -> PipelineBuilder:
        """
        Add a group of steps to execute in parallel.

        Args:
            steps: List of PipelineStep to run concurrently
            merge_strategy: How to combine outputs ('all', 'first_success', 'majority')
            timeout_seconds: Timeout for the entire group

        Returns:
            Self for chaining
        """
        group = ParallelGroup(
            steps=steps,
            merge_strategy=merge_strategy,
            timeout_seconds=timeout_seconds,
        )
        self._steps.append(group)
        self._last_step = None  # Clear last step since this is a group
        return self

    def add_conditional_step(
        self,
        condition: Callable[[dict[str, Any]], bool],
        step: PipelineStep,
        else_step: PipelineStep | None = None,
        condition_name: str = "",
    ) -> PipelineBuilder:
        """
        Add a conditional step that only executes if condition is met.

        Args:
            condition: Function that receives context dict and returns bool
            step: Step to execute if condition is True
            else_step: Optional step to execute if condition is False
            condition_name: Human-readable name for logging

        Returns:
            Self for chaining
        """
        conditional = ConditionalStep(
            condition=condition,
            step=step,
            else_step=else_step,
            condition_name=condition_name,
        )
        self._steps.append(conditional)
        self._last_step = step  # Allow chaining to modify the conditional step
        return self

    def add_router(
        self,
        router_fn: Callable[[dict[str, Any]], str],
        task: str,
        routes: dict[str, PipelineStep],
        default_route: str | None = None,
    ) -> PipelineBuilder:
        """
        Add a router step that dynamically selects agent based on context.

        Args:
            router_fn: Function that returns route key based on context
            task: Task description (shared across routes)
            routes: Dict mapping route keys to PipelineStep configurations
            default_route: Default route key if router returns unknown value

        Returns:
            Self for chaining
        """
        router = RouterStep(
            router_fn=router_fn,
            task=task,
            routes=routes,
            default_route=default_route,
        )
        self._steps.append(router)
        self._last_step = None
        return self

    def with_initial_inputs(self, inputs: dict[str, Any]) -> PipelineBuilder:
        """
        Set initial inputs for the pipeline.

        Args:
            inputs: Dict of initial input values

        Returns:
            Self for chaining
        """
        self._initial_inputs = inputs
        return self

    def build(self) -> Pipeline:
        """
        Build the pipeline definition.

        Returns:
            Complete Pipeline ready for execution
        """
        return Pipeline(
            name=self._name,
            description=self._description,
            steps=self._steps.copy(),
            initial_inputs=self._initial_inputs.copy(),
        )

    def reset(self) -> PipelineBuilder:
        """
        Reset the builder for reuse.

        Returns:
            Self for chaining
        """
        self._steps = []
        self._last_step = None
        self._initial_inputs = {}
        return self


# =============================================================================
# Pipeline Executor
# =============================================================================


class PipelineExecutor:
    """
    Executes pipelines built with PipelineBuilder.

    Handles sequential, parallel, and conditional execution patterns.
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        max_parallel: int = 5,
    ):
        """
        Initialize the executor.

        Args:
            orchestrator: AgentOrchestrator instance
            max_parallel: Maximum concurrent parallel executions
        """
        self._orchestrator = orchestrator
        self._max_parallel = max_parallel
        self._semaphore = asyncio.Semaphore(max_parallel)

    async def execute(
        self,
        pipeline: Pipeline,
        context: dict[str, Any] | None = None,
    ) -> PipelineExecutionResult:
        """
        Execute a pipeline.

        Args:
            pipeline: Pipeline definition to execute
            context: Optional execution context with additional data

        Returns:
            PipelineExecutionResult with all outputs
        """
        start_time = datetime.now()
        result = PipelineExecutionResult(pipeline_id=pipeline.pipeline_id)
        result.status = "in_progress"

        # Initialize context with initial inputs
        exec_context: dict[str, Any] = {}
        exec_context.update(pipeline.initial_inputs)
        if context:
            exec_context.update(context)

        logger.info(
            f"Executing pipeline '{pipeline.name}' ({pipeline.pipeline_id}) "
            f"with {len(pipeline.steps)} steps"
        )

        try:
            for i, step_item in enumerate(pipeline.steps):
                step_name = f"step_{i}"

                if isinstance(step_item, PipelineStep):
                    # Sequential step
                    step_result = await self._execute_step(step_item, exec_context)
                    result.step_results[step_item.output_key] = step_result
                    exec_context[step_item.output_key] = step_result

                elif isinstance(step_item, ParallelGroup):
                    # Parallel group
                    group_results = await self._execute_parallel_group(step_item, exec_context)
                    result.parallel_results[step_item.group_id] = group_results
                    # Merge results into context
                    for j, step in enumerate(step_item.steps):
                        exec_context[step.output_key] = group_results[j]

                elif isinstance(step_item, ConditionalStep):
                    # Conditional step
                    if step_item.condition(exec_context):
                        step_result = await self._execute_step(step_item.step, exec_context)
                        result.step_results[step_item.step.output_key] = step_result
                        exec_context[step_item.step.output_key] = step_result
                    elif step_item.else_step:
                        step_result = await self._execute_step(step_item.else_step, exec_context)
                        result.step_results[step_item.else_step.output_key] = step_result
                        exec_context[step_item.else_step.output_key] = step_result

                elif isinstance(step_item, RouterStep):
                    # Router step
                    route_key = step_item.router_fn(exec_context)
                    if route_key in step_item.routes:
                        step_to_execute = step_item.routes[route_key]
                    elif step_item.default_route and step_item.default_route in step_item.routes:
                        step_to_execute = step_item.routes[step_item.default_route]
                    else:
                        raise ValueError(f"Router returned unknown route: {route_key}")

                    step_result = await self._execute_step(step_to_execute, exec_context)
                    result.step_results[step_to_execute.output_key] = step_result
                    exec_context[step_to_execute.output_key] = step_result

                logger.debug(f"Completed {step_name}")

            result.status = "completed"
            result.final_output = self._create_final_output(result.step_results)

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            logger.error(f"Pipeline execution failed: {e}")

        result.total_duration_seconds = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Pipeline '{pipeline.name}' {result.status} "
            f"in {result.total_duration_seconds:.2f}s"
        )

        return result

    async def _execute_step(
        self,
        step: PipelineStep,
        context: dict[str, Any],
    ) -> AgentResult:
        """
        Execute a single pipeline step.

        Args:
            step: Step to execute
            context: Current execution context

        Returns:
            AgentResult from step execution
        """
        # Resolve input mappings
        inputs = self._resolve_inputs(step.input_mapping, context)

        # Import OrchestrationStep to use orchestrator's execution
        from .orchestrator import OrchestrationStep

        orch_step = OrchestrationStep(
            agent_type=step.agent_type,
            task=step.task,
            input_mapping=step.input_mapping,
            output_key=step.output_key,
            checkpoint_required=step.checkpoint_required,
        )

        # Get agent and execute
        agent = self._orchestrator._get_agent(step.agent_type)

        # Execute with retry logic
        last_error: Exception | None = None
        for attempt in range(step.retry_count + 1):
            try:
                return await self._orchestrator._execute_step(agent, orch_step, inputs)
            except Exception as e:
                last_error = e
                if attempt < step.retry_count:
                    logger.warning(
                        f"Step {step.step_id} failed (attempt {attempt + 1}), retrying: {e}"
                    )

        raise last_error or RuntimeError(f"Step {step.step_id} failed")

    async def _execute_parallel_group(
        self,
        group: ParallelGroup,
        context: dict[str, Any],
    ) -> list[AgentResult]:
        """
        Execute a parallel group of steps.

        Args:
            group: ParallelGroup to execute
            context: Current execution context

        Returns:
            List of AgentResult from all steps
        """
        logger.info(f"Executing parallel group '{group.group_id}' with {len(group.steps)} steps")

        async def execute_with_semaphore(step: PipelineStep) -> AgentResult:
            async with self._semaphore:
                return await self._execute_step(step, context)

        # Create tasks for all steps
        tasks = [execute_with_semaphore(step) for step in group.steps]

        # Execute with optional timeout
        if group.timeout_seconds:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=group.timeout_seconds,
            )
        else:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results based on merge strategy
        valid_results: list[AgentResult[Any]] = []
        for i, r in enumerate(results):
            if isinstance(r, BaseException):
                logger.error(f"Parallel step {group.steps[i].step_id} failed: {r}")
                if group.merge_strategy != "first_success":
                    raise r
            else:
                valid_results.append(r)

        if group.merge_strategy == "first_success" and valid_results:
            return [valid_results[0]]

        return valid_results

    def _resolve_inputs(
        self,
        mapping: dict[str, str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Resolve input mappings from context.

        Args:
            mapping: Input mapping dict
            context: Current context

        Returns:
            Dict of resolved inputs
        """
        resolved: dict[str, Any] = {}

        for input_name, source_path in mapping.items():
            try:
                parts = source_path.split(".")
                value: Any = context

                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    elif hasattr(value, "deliverable"):
                        # Handle AgentResult
                        deliverable = value.deliverable
                        if hasattr(deliverable, part):
                            value = getattr(deliverable, part)
                        elif isinstance(deliverable, dict):
                            value = deliverable.get(part)
                        else:
                            value = None
                    else:
                        value = None
                        break

                resolved[input_name] = value

            except Exception as e:
                logger.warning(f"Failed to resolve input '{input_name}': {e}")
                resolved[input_name] = None

        return resolved

    def _create_final_output(
        self,
        step_results: dict[str, AgentResult],
    ) -> dict[str, Any]:
        """
        Create final output summary from step results.

        Args:
            step_results: Results from all steps

        Returns:
            Dict with output summary
        """
        output: dict[str, Any] = {
            "deliverables": {},
            "outcomes": {},
        }

        for key, result in step_results.items():
            if hasattr(result, "deliverable") and result.deliverable:
                deliverable = result.deliverable
                if hasattr(deliverable, "to_dict"):
                    output["deliverables"][key] = deliverable.to_dict()
                else:
                    output["deliverables"][key] = str(deliverable)

            if hasattr(result, "outcome"):
                output["outcomes"][key] = result.outcome.value

        return output


# =============================================================================
# Convenience Functions
# =============================================================================


def create_research_pipeline(
    query: str,
    jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
    language: Language = Language.DE,
) -> Pipeline:
    """
    Create a standard research pipeline.

    Args:
        query: Research query
        jurisdiction: Legal jurisdiction
        language: Output language

    Returns:
        Pipeline configured for legal research
    """
    return (
        PipelineBuilder("research_pipeline", "Standard legal research workflow")
        .add_step("researcher", f"Research: {query}")
        .with_initial_inputs(
            {
                "query": query,
                "jurisdiction": jurisdiction,
                "language": language,
            }
        )
        .build()
    )


def create_full_case_pipeline(
    query: str,
    include_analysis: bool = False,
    jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
    language: Language = Language.DE,
) -> Pipeline:
    """
    Create a full case handling pipeline.

    Args:
        query: Initial case query
        include_analysis: Whether to include deep analysis step
        jurisdiction: Legal jurisdiction
        language: Output language

    Returns:
        Pipeline for complete case handling
    """
    builder = (
        PipelineBuilder("full_case_pipeline", "Complete case handling workflow")
        .with_initial_inputs(
            {
                "query": query,
                "jurisdiction": jurisdiction,
                "language": language,
            }
        )
        .add_step("researcher", f"Research legal aspects: {query}")
    )

    if include_analysis:
        builder.add_step("analyzer", "Deep analysis of research findings").with_input_mapping(
            {"research_results": "researcher_output.deliverable"}
        )

    builder.add_step("strategist", "Develop litigation strategy").with_input_mapping(
        {"research_results": "researcher_output.deliverable"}
    ).with_checkpoint()

    builder.add_step("drafter", "Draft legal document").with_input_mapping(
        {"strategy_input": "strategist_output.deliverable"}
    ).with_checkpoint()

    return builder.build()
