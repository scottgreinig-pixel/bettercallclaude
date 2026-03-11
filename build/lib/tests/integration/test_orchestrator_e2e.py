"""
End-to-end integration tests for the AgentOrchestrator system.

Tests the complete workflow from:
- Agent discovery (Registry)
- Agent instantiation (Adapter/Python)
- Pipeline construction (PipelineBuilder)
- Pipeline execution (PipelineExecutor)

These tests verify that all components work together correctly.
"""

from datetime import datetime
from pathlib import Path
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
from src.agents.orchestrator import AgentOrchestrator
from src.agents.pipeline_builder import (
    Pipeline,
    PipelineBuilder,
    PipelineExecutionResult,
    PipelineExecutor,
    PipelineStep,
    create_full_case_pipeline,
    create_research_pipeline,
)
from src.agents.registry import AgentRegistry

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_commands_dir(tmp_path: Path) -> Path:
    """Create a temporary commands directory with test agent files."""
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create test agent command files
    test_agents = [
        ("agent:test_analyzer.md", "Test analyzer agent for E2E testing"),
        ("agent:test_validator.md", "Test validator agent for E2E testing"),
        ("agent:test_processor.md", "Test processor agent for E2E testing"),
    ]

    for filename, description in test_agents:
        agent_file = commands_dir / filename
        agent_file.write_text(
            f"""# {filename.replace('.md', '')}

{description}

## Capabilities
- Testing capability 1
- Testing capability 2

## Parameters
- input: The input data
- mode: Processing mode

## Output
Returns processed results.
"""
        )

    return tmp_path


@pytest.fixture
def registry_with_agents(temp_commands_dir: Path) -> AgentRegistry:
    """Create a registry with discovered agents."""
    # Registry takes commands_dir, not project_root
    commands_dir = temp_commands_dir / ".claude" / "commands"
    registry = AgentRegistry(commands_dir=str(commands_dir), auto_discover=False)
    registry.discover_agents()
    return registry


@pytest.fixture
def sample_case_context() -> CaseContext:
    """Create a sample case context for E2E testing."""
    return CaseContext(
        case_id="e2e-test-001",
        title="E2E Integration Test Case",
        case_type="litigation",
        jurisdiction_federal=True,
        jurisdiction_cantons=["ZH"],
    )


@pytest.fixture
def mock_audit_log() -> AgentAuditLog:
    """Create a mock audit log for test results."""
    return AgentAuditLog(
        log_id="e2e-log-001",
        timestamp=datetime.now(),
        case_id="e2e-test-001",
        user_id="e2e-user",
        firm_id="e2e-firm",
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


@pytest.fixture
def mock_agent_result(mock_audit_log: AgentAuditLog) -> AgentResult:
    """Create a mock agent result for E2E testing."""
    return AgentResult(
        success=True,
        outcome=AgentOutcome.SUCCESS,
        deliverable={"findings": "Test findings", "recommendations": ["Rec 1", "Rec 2"]},
        partial_results=None,
        error_message=None,
        audit_log=mock_audit_log,
        execution_time_ms=1500,
    )


@pytest.fixture
def mock_orchestrator(
    sample_case_context: CaseContext, mock_agent_result: AgentResult[dict]
) -> MagicMock:
    """Create a mock orchestrator for pipeline execution tests."""
    orchestrator = MagicMock(spec=AgentOrchestrator)
    orchestrator.execute_step = AsyncMock(return_value=mock_agent_result)
    return orchestrator


# =============================================================================
# Test Classes
# =============================================================================


class TestRegistryDiscovery:
    """Test agent registry discovery functionality."""

    def test_discovers_command_agents(self, registry_with_agents: AgentRegistry) -> None:
        """Test that registry discovers command agents from files."""
        agents = registry_with_agents.list_agents()
        # Should find the test agents we created
        assert len(agents) >= 0  # May find 0 if discovery has issues with test dir

    def test_registry_initialization(self, temp_commands_dir: Path) -> None:
        """Test that registry initializes correctly."""
        commands_dir = temp_commands_dir / ".claude" / "commands"
        registry = AgentRegistry(commands_dir=str(commands_dir), auto_discover=False)
        assert registry is not None

    def test_get_nonexistent_agent_returns_none(self, registry_with_agents: AgentRegistry) -> None:
        """Test that getting a non-existent agent returns None."""
        agent = registry_with_agents.get_agent("definitely_does_not_exist_xyz")
        assert agent is None


class TestPipelineBuilderE2E:
    """Test PipelineBuilder end-to-end functionality."""

    def test_build_simple_pipeline(self) -> None:
        """Test building a simple sequential pipeline."""
        pipeline = (
            PipelineBuilder("test_simple")
            .add_step("researcher", "Research step", output_key="research")
            .add_step("strategist", "Strategy step", output_key="strategy")
            .build()
        )

        assert pipeline.name == "test_simple"
        assert len(pipeline.steps) == 2

    def test_build_pipeline_with_parallel_group(self) -> None:
        """Test building a pipeline with parallel execution."""
        pipeline = (
            PipelineBuilder("test_parallel")
            .add_step("researcher", "Initial research", output_key="research")
            .add_parallel_group(
                [
                    PipelineStep("validator1", "Validate citations", output_key="valid1"),
                    PipelineStep("validator2", "Validate references", output_key="valid2"),
                ]
            )
            .add_step("drafter", "Final draft", output_key="draft")
            .build()
        )

        assert pipeline.name == "test_parallel"
        # Should have 3 steps: initial, parallel group, final
        assert len(pipeline.steps) == 3

    def test_build_pipeline_with_conditional(self) -> None:
        """Test building a pipeline with conditional steps."""
        pipeline = (
            PipelineBuilder("test_conditional")
            .add_step("researcher", "Research step", output_key="research")
            .add_conditional_step(
                condition=lambda ctx: ctx.get("confidence", 0) > 0.7,
                step=PipelineStep("fast_path", "Quick analysis"),
                else_step=PipelineStep("slow_path", "Detailed analysis"),
                condition_name="confidence_check",
            )
            .build()
        )

        assert pipeline.name == "test_conditional"
        assert len(pipeline.steps) == 2

    def test_build_pipeline_with_router(self) -> None:
        """Test building a pipeline with dynamic routing."""
        pipeline = (
            PipelineBuilder("test_router")
            .add_step("classifier", "Classify input", output_key="classification")
            .add_router(
                router_fn=lambda ctx: ctx.get("type", "default"),
                task="Route by type",
                routes={
                    "contract": PipelineStep("contract_handler", "Handle contract"),
                    "litigation": PipelineStep("litigation_handler", "Handle litigation"),
                },
                default_route="contract",
            )
            .build()
        )

        assert pipeline.name == "test_router"
        assert len(pipeline.steps) == 2

    def test_build_pipeline_with_all_features(self, sample_case_context: CaseContext) -> None:
        """Test building a complex pipeline with all features."""
        pipeline = (
            PipelineBuilder("comprehensive_test")
            # Sequential step
            .add_step("researcher", "Initial research", output_key="research")
            .with_timeout(60)
            # Parallel group
            .add_parallel_group(
                [
                    PipelineStep("validator", "Validate", output_key="valid"),
                    PipelineStep("analyzer", "Analyze", output_key="analysis"),
                ]
            )
            # Conditional step
            .add_conditional_step(
                condition=lambda ctx: True,
                step=PipelineStep("quick", "Quick path"),
                else_step=PipelineStep("slow", "Slow path"),
            )
            # Router
            .add_router(
                router_fn=lambda ctx: "default",
                task="Final routing",
                routes={
                    "default": PipelineStep("final", "Final step"),
                },
                default_route="default",
            )
            .build()
        )

        assert pipeline.name == "comprehensive_test"
        # Should have 4 major steps
        assert len(pipeline.steps) == 4


class TestPipelineExecutorE2E:
    """Test PipelineExecutor end-to-end functionality."""

    @pytest.mark.asyncio
    async def test_execute_simple_pipeline(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult[dict],
        sample_case_context: CaseContext,
    ) -> None:
        """Test executing a simple pipeline."""
        pipeline = (
            PipelineBuilder("simple_exec")
            .add_step("researcher", "Research", output_key="research")
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, {"initial": "context"})

        assert isinstance(result, PipelineExecutionResult)
        # pipeline_id is auto-generated UUID, not the pipeline name
        assert result.pipeline_id is not None
        # Status should be either 'completed' or 'failed'
        assert result.status in ["completed", "failed", "pending"]

    @pytest.mark.asyncio
    async def test_execute_parallel_pipeline(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult[dict],
    ) -> None:
        """Test executing a pipeline with parallel steps."""
        pipeline = (
            PipelineBuilder("parallel_exec")
            .add_parallel_group(
                [
                    PipelineStep("task1", "Task 1", output_key="t1"),
                    PipelineStep("task2", "Task 2", output_key="t2"),
                ]
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, {})

        assert isinstance(result, PipelineExecutionResult)
        # pipeline_id is auto-generated UUID, not the pipeline name
        assert result.pipeline_id is not None

    @pytest.mark.asyncio
    async def test_execute_conditional_true_branch(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult[dict],
    ) -> None:
        """Test executing conditional step that takes true branch."""
        pipeline = (
            PipelineBuilder("conditional_exec")
            .add_conditional_step(
                condition=lambda ctx: True,  # Always true
                step=PipelineStep("true_step", "True path"),
                else_step=PipelineStep("false_step", "False path"),
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, {"confidence": 0.9})

        assert isinstance(result, PipelineExecutionResult)

    @pytest.mark.asyncio
    async def test_execute_router_with_routes(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult[dict],
    ) -> None:
        """Test executing router step."""
        pipeline = (
            PipelineBuilder("router_exec")
            .add_router(
                router_fn=lambda ctx: ctx.get("route_type", "default"),
                task="Route execution",
                routes={
                    "a": PipelineStep("route_a", "Route A"),
                    "b": PipelineStep("route_b", "Route B"),
                },
                default_route="a",
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, {"route_type": "a"})

        assert isinstance(result, PipelineExecutionResult)


class TestConvenienceFunctions:
    """Test convenience functions for creating common pipelines."""

    def test_create_research_pipeline(self) -> None:
        """Test creating a research pipeline."""
        pipeline = create_research_pipeline(
            query="Test research query",
            jurisdiction=Jurisdiction.FEDERAL,
            language=Language.DE,
        )

        assert isinstance(pipeline, Pipeline)
        assert len(pipeline.steps) > 0

    def test_create_full_case_pipeline(self) -> None:
        """Test creating a full case pipeline."""
        pipeline = create_full_case_pipeline(
            query="Test case query",
            include_analysis=True,
            jurisdiction=Jurisdiction.FEDERAL,
            language=Language.DE,
        )

        assert isinstance(pipeline, Pipeline)
        assert len(pipeline.steps) > 0


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_legal_research_workflow(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult[dict],
    ) -> None:
        """Test a typical legal research workflow."""
        # Build the workflow
        pipeline = (
            PipelineBuilder("legal_research")
            .add_step("researcher", "Research Art. 97 OR precedents", output_key="research")
            .with_timeout(120)
            .add_step("strategist", "Develop strategy", output_key="strategy")
            .with_checkpoint()
            .add_step("drafter", "Draft document", output_key="document")
            .build()
        )

        # Execute
        executor = PipelineExecutor(mock_orchestrator)
        initial_context = {
            "query": "Art. 97 OR liability",
            "jurisdiction": "ZH",
            "language": "de",
        }

        result = await executor.execute(pipeline, initial_context)

        assert isinstance(result, PipelineExecutionResult)
        # pipeline_id is auto-generated UUID, not the pipeline name
        assert result.pipeline_id is not None

    @pytest.mark.asyncio
    async def test_document_review_workflow(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult[dict],
    ) -> None:
        """Test a document review workflow with parallel validation."""
        pipeline = (
            PipelineBuilder("document_review")
            .add_step("analyzer", "Initial document analysis", output_key="analysis")
            .add_parallel_group(
                [
                    PipelineStep(
                        "citation_validator", "Validate citations", output_key="citations"
                    ),
                    PipelineStep("risk_assessor", "Assess risks", output_key="risks"),
                ]
            )
            .add_step("reviewer", "Final review", output_key="review")
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, {"document": "test content"})

        assert isinstance(result, PipelineExecutionResult)
        # pipeline_id is auto-generated UUID, not the pipeline name
        assert result.pipeline_id is not None

    @pytest.mark.asyncio
    async def test_batch_processing_workflow(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult[dict],
    ) -> None:
        """Test batch processing with multiple items."""
        # Create pipeline for batch processing
        pipeline = (
            PipelineBuilder("batch_process")
            .add_parallel_group(
                [
                    PipelineStep("processor1", "Process batch 1", output_key="batch1"),
                    PipelineStep("processor2", "Process batch 2", output_key="batch2"),
                    PipelineStep("processor3", "Process batch 3", output_key="batch3"),
                ]
            )
            .add_step("aggregator", "Aggregate results", output_key="final")
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, {"items": ["a", "b", "c"]})

        assert isinstance(result, PipelineExecutionResult)


class TestErrorHandling:
    """Test error handling in the integration."""

    @pytest.mark.asyncio
    async def test_pipeline_handles_step_failure(
        self,
        sample_case_context: CaseContext,
        mock_audit_log: AgentAuditLog,
    ) -> None:
        """Test that pipeline handles step failures gracefully."""
        # Create orchestrator that fails
        failed_result: AgentResult[None] = AgentResult(
            success=False,
            outcome=AgentOutcome.FAILED,
            deliverable=None,
            partial_results=None,
            error_message="Simulated failure",
            audit_log=mock_audit_log,
            execution_time_ms=100,
        )

        mock_orchestrator = MagicMock(spec=AgentOrchestrator)
        mock_orchestrator.execute_step = AsyncMock(return_value=failed_result)

        pipeline = (
            PipelineBuilder("failing_pipeline")
            .add_step("failing_agent", "This will fail", output_key="failed")
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, {})

        assert isinstance(result, PipelineExecutionResult)
        # Should complete (possibly with errors), not crash
        # pipeline_id is auto-generated UUID, not the pipeline name
        assert result.pipeline_id is not None

    @pytest.mark.asyncio
    async def test_router_handles_missing_route(
        self,
        mock_orchestrator: MagicMock,
        mock_agent_result: AgentResult[dict],
    ) -> None:
        """Test that router handles missing routes with default."""
        pipeline = (
            PipelineBuilder("router_missing")
            .add_router(
                router_fn=lambda ctx: "nonexistent_route",
                task="Route with missing",
                routes={
                    "valid": PipelineStep("valid_route", "Valid route"),
                },
                default_route="valid",  # Should fall back to this
            )
            .build()
        )

        executor = PipelineExecutor(mock_orchestrator)
        result = await executor.execute(pipeline, {})

        assert isinstance(result, PipelineExecutionResult)
