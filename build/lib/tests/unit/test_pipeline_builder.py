"""
Unit tests for the PipelineBuilder module.

Tests:
- PipelineStep dataclass
- ParallelGroup dataclass
- ConditionalStep dataclass
- RouterStep dataclass
- Pipeline dataclass
- PipelineBuilder fluent API
- PipelineExecutor execution patterns
- Convenience functions
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.base import (
    AgentAuditLog,
    AgentOutcome,
    AgentResult,
    AutonomyMode,
    CaseContext,
)
from src.agents.models.shared import Jurisdiction, Language
from src.agents.pipeline_builder import (
    ConditionalStep,
    ParallelGroup,
    Pipeline,
    PipelineBuilder,
    PipelineExecutor,
    PipelineStep,
    RouterStep,
    create_full_case_pipeline,
    create_research_pipeline,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_case_context() -> CaseContext:
    """Create a sample case context for testing."""
    return CaseContext(
        case_id="test-case-001",
        title="Test Contract Dispute",
        case_type="litigation",
        jurisdiction_federal=True,
        jurisdiction_cantons=["ZH"],
    )


@pytest.fixture
def mock_agent_result() -> AgentResult:
    """Create a mock agent result."""
    from datetime import datetime

    audit_log = AgentAuditLog(
        log_id="test-log-001",
        timestamp=datetime.now(),
        case_id="test-case-001",
        user_id="test-user",
        firm_id="test-firm",
        agent_id="test-agent",
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
    return AgentResult(
        success=True,
        outcome=AgentOutcome.SUCCESS,
        deliverable={"findings": "Test findings", "recommendations": ["Rec 1", "Rec 2"]},
        partial_results=None,
        error_message=None,
        audit_log=audit_log,
        execution_time_ms=1500,
    )


@pytest.fixture
def mock_orchestrator(mock_agent_result: AgentResult) -> MagicMock:
    """Create a mock orchestrator."""
    orchestrator = MagicMock()

    # Mock agent
    mock_agent = MagicMock()
    mock_agent.execute = AsyncMock(return_value=mock_agent_result)
    orchestrator._get_agent = MagicMock(return_value=mock_agent)

    # Mock _execute_step
    orchestrator._execute_step = AsyncMock(return_value=mock_agent_result)

    # Mock config
    orchestrator.config = MagicMock()
    orchestrator.config.language = Language.DE
    orchestrator.config.jurisdiction = Jurisdiction.FEDERAL

    return orchestrator


# =============================================================================
# PipelineStep Tests
# =============================================================================


class TestPipelineStep:
    """Tests for PipelineStep dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        step = PipelineStep(agent_type="researcher", task="Research task")

        assert step.agent_type == "researcher"
        assert step.task == "Research task"
        assert step.step_id.startswith("researcher_")
        assert step.output_key == "researcher_output"
        assert step.input_mapping == {}
        assert step.checkpoint_required is False
        assert step.timeout_seconds is None
        assert step.retry_count == 0

    def test_custom_values(self) -> None:
        """Test with custom values."""
        step = PipelineStep(
            agent_type="strategist",
            task="Strategy task",
            step_id="custom_step",
            output_key="custom_output",
            input_mapping={"data": "previous.output"},
            checkpoint_required=True,
            timeout_seconds=60,
            retry_count=3,
        )

        assert step.step_id == "custom_step"
        assert step.output_key == "custom_output"
        assert step.input_mapping == {"data": "previous.output"}
        assert step.checkpoint_required is True
        assert step.timeout_seconds == 60
        assert step.retry_count == 3

    def test_auto_generated_ids(self) -> None:
        """Test that auto-generated IDs are unique."""
        step1 = PipelineStep(agent_type="researcher", task="Task 1")
        step2 = PipelineStep(agent_type="researcher", task="Task 2")

        assert step1.step_id != step2.step_id


# =============================================================================
# ParallelGroup Tests
# =============================================================================


class TestParallelGroup:
    """Tests for ParallelGroup dataclass."""

    def test_default_values(self) -> None:
        """Test default values for parallel group."""
        steps = [
            PipelineStep(agent_type="researcher", task="Research 1"),
            PipelineStep(agent_type="analyzer", task="Analyze 1"),
        ]
        group = ParallelGroup(steps=steps)

        assert len(group.steps) == 2
        assert group.group_id.startswith("parallel_")
        assert group.merge_strategy == "all"
        assert group.timeout_seconds is None

    def test_custom_values(self) -> None:
        """Test with custom values."""
        steps = [PipelineStep(agent_type="researcher", task="Research")]
        group = ParallelGroup(
            steps=steps,
            group_id="custom_group",
            merge_strategy="first_success",
            timeout_seconds=120,
        )

        assert group.group_id == "custom_group"
        assert group.merge_strategy == "first_success"
        assert group.timeout_seconds == 120


# =============================================================================
# ConditionalStep Tests
# =============================================================================


class TestConditionalStep:
    """Tests for ConditionalStep dataclass."""

    def test_basic_conditional(self) -> None:
        """Test basic conditional step."""

        def condition(ctx: dict) -> bool:
            return bool(ctx.get("needs_analysis", False))

        step = PipelineStep(agent_type="analyzer", task="Analyze")

        conditional = ConditionalStep(
            condition=condition,
            step=step,
            condition_name="needs_analysis_check",
        )

        assert callable(conditional.condition)
        assert conditional.step.agent_type == "analyzer"
        assert conditional.else_step is None
        assert conditional.condition_name == "needs_analysis_check"

    def test_conditional_with_else(self) -> None:
        """Test conditional with else branch."""

        def condition(ctx: dict) -> bool:
            return bool(ctx.get("complex", False))

        if_step = PipelineStep(agent_type="analyzer", task="Deep analyze")
        else_step = PipelineStep(agent_type="researcher", task="Quick research")

        conditional = ConditionalStep(
            condition=condition,
            step=if_step,
            else_step=else_step,
        )

        assert conditional.else_step is not None
        assert conditional.else_step.agent_type == "researcher"

    def test_condition_evaluation(self) -> None:
        """Test that condition evaluation works."""

        def condition(ctx: dict) -> bool:
            value: int = ctx.get("value", 0)
            return value > 5

        conditional = ConditionalStep(
            condition=condition,
            step=PipelineStep(agent_type="analyzer", task="Analyze"),
        )

        assert conditional.condition({"value": 10}) is True
        assert conditional.condition({"value": 3}) is False
        assert conditional.condition({}) is False


# =============================================================================
# RouterStep Tests
# =============================================================================


class TestRouterStep:
    """Tests for RouterStep dataclass."""

    def test_router_step_creation(self) -> None:
        """Test router step creation."""

        def router_fn(ctx: dict) -> str:
            return str(ctx.get("route", "default"))

        routes = {
            "research": PipelineStep(agent_type="researcher", task="Research"),
            "analyze": PipelineStep(agent_type="analyzer", task="Analyze"),
        }

        router = RouterStep(
            router_fn=router_fn,
            task="Dynamic task",
            routes=routes,
            default_route="research",
        )

        assert callable(router.router_fn)
        assert router.task == "Dynamic task"
        assert len(router.routes) == 2
        assert router.default_route == "research"

    def test_router_function_evaluation(self) -> None:
        """Test router function returns correct route."""

        def router_fn(ctx: dict) -> str:
            return "complex" if ctx.get("complexity", 0) > 5 else "simple"

        router = RouterStep(
            router_fn=router_fn,
            task="Task",
            routes={
                "complex": PipelineStep(agent_type="analyzer", task="Complex"),
                "simple": PipelineStep(agent_type="researcher", task="Simple"),
            },
        )

        assert router.router_fn({"complexity": 10}) == "complex"
        assert router.router_fn({"complexity": 2}) == "simple"


# =============================================================================
# Pipeline Tests
# =============================================================================


class TestPipeline:
    """Tests for Pipeline dataclass."""

    def test_empty_pipeline(self) -> None:
        """Test empty pipeline creation."""
        pipeline = Pipeline()

        assert pipeline.pipeline_id is not None
        assert len(pipeline.pipeline_id) == 8
        assert pipeline.name == ""
        assert pipeline.steps == []
        assert len(pipeline) == 0

    def test_pipeline_with_steps(self) -> None:
        """Test pipeline with steps."""
        steps: list[PipelineStep | ParallelGroup | ConditionalStep | RouterStep] = [
            PipelineStep(agent_type="researcher", task="Research"),
            PipelineStep(agent_type="strategist", task="Strategize"),
        ]

        pipeline = Pipeline(
            name="test_pipeline",
            description="Test description",
            steps=steps,
        )

        assert pipeline.name == "test_pipeline"
        assert pipeline.description == "Test description"
        assert len(pipeline) == 2

    def test_pipeline_with_initial_inputs(self) -> None:
        """Test pipeline with initial inputs."""
        pipeline = Pipeline(
            name="test",
            initial_inputs={"query": "Test query", "language": "DE"},
        )

        assert pipeline.initial_inputs["query"] == "Test query"
        assert pipeline.initial_inputs["language"] == "DE"


# =============================================================================
# PipelineBuilder Tests
# =============================================================================


class TestPipelineBuilder:
    """Tests for PipelineBuilder fluent API."""

    def test_basic_sequential_pipeline(self) -> None:
        """Test building a basic sequential pipeline."""
        pipeline = (
            PipelineBuilder("test_pipeline", "Test description")
            .add_step("researcher", "Research task")
            .add_step("strategist", "Strategy task")
            .add_step("drafter", "Draft task")
            .build()
        )

        assert pipeline.name == "test_pipeline"
        assert len(pipeline.steps) == 3
        assert all(isinstance(s, PipelineStep) for s in pipeline.steps)

    def test_step_with_input_mapping(self) -> None:
        """Test adding input mapping to steps."""
        pipeline = (
            PipelineBuilder()
            .add_step("researcher", "Research")
            .add_step("strategist", "Strategy")
            .with_input_mapping({"research_data": "researcher_output.findings"})
            .build()
        )

        strategist_step = pipeline.steps[1]
        assert isinstance(strategist_step, PipelineStep)
        assert strategist_step.input_mapping == {"research_data": "researcher_output.findings"}

    def test_step_with_checkpoint(self) -> None:
        """Test adding checkpoint to step."""
        pipeline = PipelineBuilder().add_step("strategist", "Strategy").with_checkpoint().build()

        step = pipeline.steps[0]
        assert isinstance(step, PipelineStep)
        assert step.checkpoint_required is True

    def test_step_with_timeout(self) -> None:
        """Test adding timeout to step."""
        pipeline = PipelineBuilder().add_step("researcher", "Research").with_timeout(120).build()

        step = pipeline.steps[0]
        assert isinstance(step, PipelineStep)
        assert step.timeout_seconds == 120

    def test_step_with_retry(self) -> None:
        """Test adding retry count to step."""
        pipeline = PipelineBuilder().add_step("researcher", "Research").with_retry(3).build()

        step = pipeline.steps[0]
        assert isinstance(step, PipelineStep)
        assert step.retry_count == 3

    def test_parallel_group(self) -> None:
        """Test adding parallel group."""
        pipeline = (
            PipelineBuilder()
            .add_parallel_group(
                [
                    PipelineStep(agent_type="researcher", task="Research 1"),
                    PipelineStep(agent_type="analyzer", task="Analyze 1"),
                ],
                merge_strategy="first_success",
                timeout_seconds=60,
            )
            .build()
        )

        assert len(pipeline.steps) == 1
        group = pipeline.steps[0]
        assert isinstance(group, ParallelGroup)
        assert len(group.steps) == 2
        assert group.merge_strategy == "first_success"

    def test_conditional_step(self) -> None:
        """Test adding conditional step."""

        def condition(ctx: dict) -> bool:
            return bool(ctx.get("deep_analysis", False))

        pipeline = (
            PipelineBuilder()
            .add_conditional_step(
                condition=condition,
                step=PipelineStep(agent_type="analyzer", task="Deep analysis"),
                condition_name="deep_analysis_check",
            )
            .build()
        )

        assert len(pipeline.steps) == 1
        cond = pipeline.steps[0]
        assert isinstance(cond, ConditionalStep)
        assert cond.condition_name == "deep_analysis_check"

    def test_conditional_step_with_else(self) -> None:
        """Test conditional step with else branch."""

        def condition(ctx: dict) -> bool:
            complexity: int = ctx.get("complexity", 0)
            return complexity > 5

        pipeline = (
            PipelineBuilder()
            .add_conditional_step(
                condition=condition,
                step=PipelineStep(agent_type="analyzer", task="Complex"),
                else_step=PipelineStep(agent_type="researcher", task="Simple"),
            )
            .build()
        )

        cond = pipeline.steps[0]
        assert isinstance(cond, ConditionalStep)
        assert cond.else_step is not None

    def test_router_step(self) -> None:
        """Test adding router step."""

        def router_fn(ctx: dict) -> str:
            return str(ctx.get("route", "default"))

        pipeline = (
            PipelineBuilder()
            .add_router(
                router_fn=router_fn,
                task="Dynamic routing",
                routes={
                    "research": PipelineStep(agent_type="researcher", task="Research"),
                    "analyze": PipelineStep(agent_type="analyzer", task="Analyze"),
                },
                default_route="research",
            )
            .build()
        )

        assert len(pipeline.steps) == 1
        router = pipeline.steps[0]
        assert isinstance(router, RouterStep)
        assert len(router.routes) == 2

    def test_initial_inputs(self) -> None:
        """Test setting initial inputs."""
        pipeline = (
            PipelineBuilder()
            .with_initial_inputs({"query": "Test", "jurisdiction": Jurisdiction.ZH})
            .add_step("researcher", "Research")
            .build()
        )

        assert pipeline.initial_inputs["query"] == "Test"
        assert pipeline.initial_inputs["jurisdiction"] == Jurisdiction.ZH

    def test_builder_reset(self) -> None:
        """Test builder reset functionality."""
        builder = PipelineBuilder("first")
        builder.add_step("researcher", "Task 1")
        builder.build()

        builder.reset()
        pipeline = builder.add_step("strategist", "Task 2").build()

        assert len(pipeline.steps) == 1
        step = pipeline.steps[0]
        assert isinstance(step, PipelineStep)
        assert step.agent_type == "strategist"

    def test_method_chaining_no_step_errors(self) -> None:
        """Test that method chaining without step raises error."""
        builder = PipelineBuilder()

        with pytest.raises(ValueError, match="No step to add"):
            builder.with_input_mapping({})

        with pytest.raises(ValueError, match="No step to add"):
            builder.with_checkpoint()

        with pytest.raises(ValueError, match="No step to add"):
            builder.with_timeout(60)

        with pytest.raises(ValueError, match="No step to add"):
            builder.with_retry(3)

    def test_complex_pipeline(self) -> None:
        """Test building a complex mixed pipeline."""
        pipeline = (
            PipelineBuilder("complex_pipeline", "Complex workflow")
            .add_step("researcher", "Initial research")
            .add_parallel_group(
                [
                    PipelineStep(agent_type="analyzer", task="Analyze 1"),
                    PipelineStep(agent_type="evaluator", task="Evaluate 1"),
                ]
            )
            .add_conditional_step(
                condition=lambda ctx: ctx.get("risk", 0) > 5,
                step=PipelineStep(agent_type="reviewer", task="Risk review"),
            )
            .add_step("strategist", "Final strategy")
            .with_checkpoint()
            .add_step("drafter", "Draft document")
            .build()
        )

        assert pipeline.name == "complex_pipeline"
        assert len(pipeline.steps) == 5

        assert isinstance(pipeline.steps[0], PipelineStep)
        assert isinstance(pipeline.steps[1], ParallelGroup)
        assert isinstance(pipeline.steps[2], ConditionalStep)
        assert isinstance(pipeline.steps[3], PipelineStep)
        assert isinstance(pipeline.steps[4], PipelineStep)


# =============================================================================
# PipelineExecutor Tests
# =============================================================================


class TestPipelineExecutor:
    """Tests for PipelineExecutor."""

    @pytest.mark.asyncio
    async def test_execute_sequential_pipeline(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult,
    ) -> None:
        """Test executing a sequential pipeline."""
        pipeline = (
            PipelineBuilder("test")
            .add_step("researcher", "Research")
            .add_step("strategist", "Strategy")
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline)

        assert result.status == "completed"
        assert len(result.step_results) == 2
        assert mock_orchestrator._execute_step.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_initial_inputs(
        self,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test execution with initial inputs."""
        pipeline = (
            PipelineBuilder()
            .with_initial_inputs({"query": "Test query"})
            .add_step("researcher", "Research")
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline)

        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_parallel_group(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult,
    ) -> None:
        """Test executing a parallel group."""
        pipeline = (
            PipelineBuilder()
            .add_parallel_group(
                [
                    PipelineStep(agent_type="researcher", task="Research 1"),
                    PipelineStep(agent_type="analyzer", task="Analyze 1"),
                ]
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator, max_parallel=5)
        result = await executor.execute(pipeline)

        assert result.status == "completed"
        assert len(result.parallel_results) == 1

    @pytest.mark.asyncio
    async def test_execute_conditional_true(
        self,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test conditional step when condition is true."""
        condition_step = PipelineStep(agent_type="analyzer", task="Analyze")

        pipeline = (
            PipelineBuilder()
            .add_conditional_step(
                condition=lambda ctx: ctx.get("needs_analysis", False),
                step=condition_step,
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(
            pipeline,
            context={"needs_analysis": True},
        )

        assert result.status == "completed"
        assert "analyzer_output" in result.step_results

    @pytest.mark.asyncio
    async def test_execute_conditional_false_with_else(
        self,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test conditional step with else branch when condition is false."""
        pipeline = (
            PipelineBuilder()
            .add_conditional_step(
                condition=lambda ctx: ctx.get("complex", False),
                step=PipelineStep(agent_type="analyzer", task="Complex"),
                else_step=PipelineStep(agent_type="researcher", task="Simple"),
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(
            pipeline,
            context={"complex": False},
        )

        assert result.status == "completed"
        assert "researcher_output" in result.step_results

    @pytest.mark.asyncio
    async def test_execute_router(
        self,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test router step execution."""
        pipeline = (
            PipelineBuilder()
            .add_router(
                router_fn=lambda ctx: ctx.get("route", "default"),
                task="Routed task",
                routes={
                    "research": PipelineStep(agent_type="researcher", task="Research"),
                    "analyze": PipelineStep(agent_type="analyzer", task="Analyze"),
                },
                default_route="research",
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)

        # Test routing to 'analyze'
        result = await executor.execute(pipeline, context={"route": "analyze"})
        assert result.status == "completed"
        assert "analyzer_output" in result.step_results

    @pytest.mark.asyncio
    async def test_execute_router_default_route(
        self,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test router with unknown route falls back to default."""
        pipeline = (
            PipelineBuilder()
            .add_router(
                router_fn=lambda ctx: ctx.get("route", "unknown"),
                task="Task",
                routes={
                    "research": PipelineStep(agent_type="researcher", task="Research"),
                },
                default_route="research",
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, context={"route": "invalid"})

        assert result.status == "completed"
        assert "researcher_output" in result.step_results

    @pytest.mark.asyncio
    async def test_execute_router_no_default_raises(
        self,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test router without default raises error for unknown route."""
        pipeline = (
            PipelineBuilder()
            .add_router(
                router_fn=lambda ctx: "unknown_route",
                task="Task",
                routes={
                    "research": PipelineStep(agent_type="researcher", task="Research"),
                },
                default_route=None,
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline)

        assert result.status == "failed"
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_execute_handles_step_failure(
        self,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test that executor handles step failure."""
        mock_orchestrator._execute_step = AsyncMock(side_effect=RuntimeError("Step failed"))

        pipeline = PipelineBuilder().add_step("researcher", "Research").build()

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline)

        assert result.status == "failed"
        assert "Step failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_execution_timing(
        self,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test that execution timing is recorded."""
        pipeline = PipelineBuilder().add_step("researcher", "Research").build()

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline)

        assert result.total_duration_seconds >= 0
        assert result.created_at is not None


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience pipeline creation functions."""

    def test_create_research_pipeline(self) -> None:
        """Test create_research_pipeline function."""
        pipeline = create_research_pipeline(
            query="Contract breach liability",
            jurisdiction=Jurisdiction.ZH,
            language=Language.DE,
        )

        assert pipeline.name == "research_pipeline"
        assert len(pipeline.steps) == 1
        assert pipeline.initial_inputs["query"] == "Contract breach liability"
        assert pipeline.initial_inputs["jurisdiction"] == Jurisdiction.ZH

    def test_create_full_case_pipeline_basic(self) -> None:
        """Test create_full_case_pipeline without analysis."""
        pipeline = create_full_case_pipeline(
            query="Employment dispute",
            include_analysis=False,
        )

        assert pipeline.name == "full_case_pipeline"
        # researcher + strategist + drafter = 3
        assert len(pipeline.steps) == 3

        step_types = [s.agent_type for s in pipeline.steps if isinstance(s, PipelineStep)]
        assert "researcher" in step_types
        assert "strategist" in step_types
        assert "drafter" in step_types

    def test_create_full_case_pipeline_with_analysis(self) -> None:
        """Test create_full_case_pipeline with analysis step."""
        pipeline = create_full_case_pipeline(
            query="Complex merger case",
            include_analysis=True,
        )

        # researcher + analyzer + strategist + drafter = 4
        assert len(pipeline.steps) == 4

        step_types = [s.agent_type for s in pipeline.steps if isinstance(s, PipelineStep)]
        assert "analyzer" in step_types


# =============================================================================
# Integration-Style Tests
# =============================================================================


class TestPipelineBuilderIntegration:
    """Integration-style tests for pipeline builder patterns."""

    def test_full_workflow_pipeline_structure(self) -> None:
        """Test building a complete workflow pipeline."""
        pipeline = (
            PipelineBuilder("legal_workflow", "Complete legal case workflow")
            .with_initial_inputs(
                {
                    "query": "Contract dispute",
                    "jurisdiction": Jurisdiction.FEDERAL,
                    "language": Language.DE,
                }
            )
            # Phase 1: Research
            .add_step("researcher", "Research precedents and law")
            .with_timeout(300)
            # Phase 2: Parallel analysis
            .add_parallel_group(
                [
                    PipelineStep(agent_type="analyzer", task="Contract analysis"),
                    PipelineStep(agent_type="evaluator", task="Risk evaluation"),
                ]
            )
            # Phase 3: Conditional review
            .add_conditional_step(
                condition=lambda ctx: ctx.get("risk_level", 0) > 7,
                step=PipelineStep(agent_type="reviewer", task="Expert review"),
            )
            # Phase 4: Strategy with checkpoint
            .add_step("strategist", "Develop strategy")
            .with_input_mapping(
                {
                    "research": "researcher_output",
                    "analysis": "analyzer_output",
                }
            )
            .with_checkpoint()
            # Phase 5: Draft
            .add_step("drafter", "Draft legal document")
            .with_input_mapping({"strategy": "strategist_output"})
            .with_checkpoint()
            .build()
        )

        # Verify structure
        assert pipeline.name == "legal_workflow"
        assert len(pipeline.steps) == 5

        # Verify initial inputs
        assert pipeline.initial_inputs["query"] == "Contract dispute"

        # Verify step types
        assert isinstance(pipeline.steps[0], PipelineStep)  # researcher
        assert isinstance(pipeline.steps[1], ParallelGroup)  # parallel
        assert isinstance(pipeline.steps[2], ConditionalStep)  # conditional
        assert isinstance(pipeline.steps[3], PipelineStep)  # strategist
        assert isinstance(pipeline.steps[4], PipelineStep)  # drafter

        # Verify timeout on researcher
        assert pipeline.steps[0].timeout_seconds == 300

        # Verify parallel group
        parallel = pipeline.steps[1]
        assert isinstance(parallel, ParallelGroup)
        assert len(parallel.steps) == 2

        # Verify checkpoint on strategist and drafter
        assert pipeline.steps[3].checkpoint_required is True
        assert pipeline.steps[4].checkpoint_required is True

    def test_branching_pipeline_structure(self) -> None:
        """Test pipeline with routing logic."""
        pipeline = (
            PipelineBuilder("branching_workflow")
            .add_step("researcher", "Initial research")
            .add_router(
                router_fn=lambda ctx: ("complex" if ctx.get("complexity", 0) > 5 else "simple"),
                task="Process based on complexity",
                routes={
                    "complex": PipelineStep(
                        agent_type="analyzer",
                        task="Deep analysis",
                    ),
                    "simple": PipelineStep(
                        agent_type="evaluator",
                        task="Quick evaluation",
                    ),
                },
                default_route="simple",
            )
            .add_step("drafter", "Final document")
            .build()
        )

        assert len(pipeline.steps) == 3
        assert isinstance(pipeline.steps[1], RouterStep)

        router = pipeline.steps[1]
        assert "complex" in router.routes
        assert "simple" in router.routes
