"""
Unit tests for AgentOrchestrator with registry integration.

Tests the orchestrator's ability to manage both Python and command-based agents
through the AgentRegistry and CommandAgentAdapter.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base import AutonomyMode, CaseContext
from src.agents.command_adapter import CommandAgentAdapter
from src.agents.orchestrator import (
    AgentOrchestrator,
    OrchestrationStep,
    PipelineConfig,
    PipelineResult,
    PipelineStatus,
)
from src.agents.registry import AgentCategory, AgentDescriptor

if TYPE_CHECKING:
    pass


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
def pipeline_config() -> PipelineConfig:
    """Create a sample pipeline config."""
    return PipelineConfig(
        autonomy_mode=AutonomyMode.CAUTIOUS,
        fail_fast=True,
        max_retries=2,
    )


@pytest.fixture
def command_descriptor() -> AgentDescriptor:
    """Create a command agent descriptor for testing."""
    return AgentDescriptor(
        agent_id="compliance",
        name="Compliance Agent",
        version="1.0.0",
        description="Compliance analysis agent",
        agent_type="command",
        category=AgentCategory.RESEARCH,
        command_path="/test/commands/agent:compliance.md",
        command_name="/agent:compliance",
    )


@pytest.fixture
def python_descriptor() -> AgentDescriptor:
    """Create a Python agent descriptor for testing."""
    return AgentDescriptor(
        agent_id="researcher",
        name="ResearcherAgent",
        version="1.0.0",
        description="Legal research agent",
        agent_type="python",
        category=AgentCategory.RESEARCH,
        module_path="src.agents.researcher",
        class_name="ResearcherAgent",
    )


@pytest.fixture
def mock_registry(
    command_descriptor: AgentDescriptor, python_descriptor: AgentDescriptor
) -> Generator[None, None, None]:
    """Create a mock registry with test agents."""
    with patch(
        "src.agents.orchestrator.AgentOrchestrator.registry",
        new_callable=lambda: property(
            lambda self: MagicMock(
                list_agents=MagicMock(return_value=[python_descriptor, command_descriptor]),
                get_agent=MagicMock(
                    side_effect=lambda x: {
                        "researcher": python_descriptor,
                        "compliance": command_descriptor,
                    }.get(x)
                ),
                __len__=MagicMock(return_value=2),
            )
        ),
    ):
        yield


# =============================================================================
# Test: Orchestrator Initialization
# =============================================================================


class TestOrchestratorInitialization:
    """Tests for AgentOrchestrator initialization."""

    def test_default_initialization(self) -> None:
        """Test orchestrator initializes with defaults."""
        orchestrator = AgentOrchestrator()

        assert orchestrator.autonomy_mode == AutonomyMode.CAUTIOUS
        assert orchestrator.case_context is None
        assert orchestrator.config is not None
        assert orchestrator.VERSION == "2.0.0"

    def test_initialization_with_params(
        self, sample_case_context: CaseContext, pipeline_config: PipelineConfig
    ) -> None:
        """Test orchestrator initialization with parameters."""
        orchestrator = AgentOrchestrator(
            autonomy_mode=AutonomyMode.AUTONOMOUS,
            case_context=sample_case_context,
            config=pipeline_config,
        )

        assert orchestrator.autonomy_mode == AutonomyMode.AUTONOMOUS
        assert orchestrator.case_context == sample_case_context
        assert orchestrator.config == pipeline_config

    def test_initialization_with_commands_dir(self, tmp_path: Path) -> None:
        """Test orchestrator initialization with commands directory."""
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()

        orchestrator = AgentOrchestrator(commands_dir=commands_dir)

        assert orchestrator._commands_dir == commands_dir


# =============================================================================
# Test: Registry Integration
# =============================================================================


class TestRegistryIntegration:
    """Tests for registry integration with orchestrator."""

    def test_registry_lazy_initialization(self) -> None:
        """Test that registry is lazily initialized."""
        orchestrator = AgentOrchestrator()

        # Registry should not be initialized yet
        assert orchestrator._registry is None

        # Access registry triggers initialization
        _ = orchestrator.registry

        # Now it should be initialized
        assert orchestrator._registry is not None

    def test_agent_types_returns_all_agents(self) -> None:
        """Test AGENT_TYPES property returns all registered agents."""
        orchestrator = AgentOrchestrator()
        agent_types = orchestrator.AGENT_TYPES

        # Should include both Python and command agents
        assert "researcher" in agent_types
        assert "strategist" in agent_types
        assert "drafter" in agent_types
        # And at least some command agents (from actual registry)
        assert len(agent_types) >= 3  # At minimum the Python agents

    def test_get_agent_info_python_agent(self) -> None:
        """Test get_agent_info for Python agent."""
        orchestrator = AgentOrchestrator()
        info = orchestrator.get_agent_info("researcher")

        assert info["agent_id"] == "researcher"
        assert info["agent_type"] == "python"
        assert info["is_python_agent"] is True

    def test_get_agent_info_command_agent(self) -> None:
        """Test get_agent_info for command agent (if available)."""
        orchestrator = AgentOrchestrator()

        # Get any available command agent
        command_agents = [
            a for a in orchestrator.AGENT_TYPES if a not in ["researcher", "strategist", "drafter"]
        ]

        if command_agents:
            info = orchestrator.get_agent_info(command_agents[0])
            assert info["agent_type"] == "command"
            assert info["is_python_agent"] is False

    def test_get_agent_info_unknown_agent(self) -> None:
        """Test get_agent_info for unknown agent returns empty dict."""
        orchestrator = AgentOrchestrator()
        info = orchestrator.get_agent_info("nonexistent")

        assert info == {}


# =============================================================================
# Test: Agent Creation
# =============================================================================


class TestAgentCreation:
    """Tests for agent creation through _get_agent."""

    def test_get_python_agent_researcher(self) -> None:
        """Test creating Python researcher agent."""
        orchestrator = AgentOrchestrator()
        agent = orchestrator._get_agent("researcher")

        assert agent is not None
        assert type(agent).__name__ == "ResearcherAgent"

    def test_get_python_agent_strategist(self) -> None:
        """Test creating Python strategist agent."""
        orchestrator = AgentOrchestrator()
        agent = orchestrator._get_agent("strategist")

        assert agent is not None
        assert type(agent).__name__ == "StrategistAgent"

    def test_get_python_agent_drafter(self) -> None:
        """Test creating Python drafter agent."""
        orchestrator = AgentOrchestrator()
        agent = orchestrator._get_agent("drafter")

        assert agent is not None
        assert type(agent).__name__ == "DrafterAgent"

    def test_get_command_agent(self) -> None:
        """Test creating command-based agent."""
        orchestrator = AgentOrchestrator()

        # Get any available command agent
        command_agents = [
            a for a in orchestrator.AGENT_TYPES if a not in ["researcher", "strategist", "drafter"]
        ]

        if command_agents:
            agent = orchestrator._get_agent(command_agents[0])
            assert isinstance(agent, CommandAgentAdapter)

    def test_agent_caching(self) -> None:
        """Test that agents are cached after creation."""
        orchestrator = AgentOrchestrator()

        agent1 = orchestrator._get_agent("researcher")
        agent2 = orchestrator._get_agent("researcher")

        assert agent1 is agent2  # Same instance

    def test_get_unknown_agent_raises_error(self) -> None:
        """Test that unknown agent type raises ValueError."""
        orchestrator = AgentOrchestrator()

        with pytest.raises(ValueError) as exc_info:
            orchestrator._get_agent("nonexistent_agent")

        assert "Unknown agent type: nonexistent_agent" in str(exc_info.value)
        assert "Available agents:" in str(exc_info.value)


# =============================================================================
# Test: Python Agent Creation Methods
# =============================================================================


class TestPythonAgentCreation:
    """Tests for _create_python_agent method."""

    def test_create_python_researcher(self) -> None:
        """Test creating researcher via _create_python_agent."""
        orchestrator = AgentOrchestrator(autonomy_mode=AutonomyMode.AUTONOMOUS)
        agent = orchestrator._create_python_agent("researcher")

        assert type(agent).__name__ == "ResearcherAgent"
        assert agent.autonomy_mode == AutonomyMode.AUTONOMOUS

    def test_create_python_strategist(self) -> None:
        """Test creating strategist via _create_python_agent."""
        orchestrator = AgentOrchestrator(autonomy_mode=AutonomyMode.CAUTIOUS)
        agent = orchestrator._create_python_agent("strategist")

        assert type(agent).__name__ == "StrategistAgent"
        assert agent.autonomy_mode == AutonomyMode.CAUTIOUS

    def test_create_python_drafter(self) -> None:
        """Test creating drafter via _create_python_agent."""
        orchestrator = AgentOrchestrator()
        agent = orchestrator._create_python_agent("drafter")

        assert type(agent).__name__ == "DrafterAgent"

    def test_create_unknown_python_agent_raises_error(self) -> None:
        """Test that unknown Python agent raises ValueError."""
        orchestrator = AgentOrchestrator()

        with pytest.raises(ValueError) as exc_info:
            orchestrator._create_python_agent("unknown")

        assert "Unknown Python agent type: unknown" in str(exc_info.value)


# =============================================================================
# Test: Command Agent Creation Methods
# =============================================================================


class TestCommandAgentCreation:
    """Tests for _create_command_agent method."""

    def test_create_command_agent_success(self) -> None:
        """Test creating command agent via _create_command_agent."""
        orchestrator = AgentOrchestrator()

        # Get any available command agent
        command_agents = [
            a for a in orchestrator.AGENT_TYPES if a not in ["researcher", "strategist", "drafter"]
        ]

        if command_agents:
            agent = orchestrator._create_command_agent(command_agents[0])
            assert isinstance(agent, CommandAgentAdapter)
            assert agent.agent_id == command_agents[0]

    def test_create_command_agent_not_found(self) -> None:
        """Test creating non-existent command agent raises error."""
        orchestrator = AgentOrchestrator()

        with pytest.raises(ValueError) as exc_info:
            orchestrator._create_command_agent("nonexistent")

        assert "Unknown agent type: nonexistent" in str(exc_info.value)

    def test_create_command_agent_wrong_type(self) -> None:
        """Test creating Python agent as command raises error."""
        orchestrator = AgentOrchestrator()

        # "researcher" is a Python agent, not a command agent
        with pytest.raises(ValueError) as exc_info:
            orchestrator._create_command_agent("researcher")

        assert "is not a command-based agent" in str(exc_info.value)


# =============================================================================
# Test: OrchestrationStep
# =============================================================================


class TestOrchestrationStep:
    """Tests for OrchestrationStep dataclass."""

    def test_step_default_output_key(self) -> None:
        """Test that output_key defaults to agent_type_output."""
        step = OrchestrationStep(
            agent_type="researcher",
            task="Research task",
        )

        assert step.output_key == "researcher_output"

    def test_step_custom_output_key(self) -> None:
        """Test custom output_key is preserved."""
        step = OrchestrationStep(
            agent_type="researcher",
            task="Research task",
            output_key="custom_key",
        )

        assert step.output_key == "custom_key"

    def test_step_with_input_mapping(self) -> None:
        """Test step with input mapping."""
        step = OrchestrationStep(
            agent_type="strategist",
            task="Strategy task",
            input_mapping={"research": "research_output.findings"},
        )

        assert step.input_mapping == {"research": "research_output.findings"}

    def test_step_with_condition(self) -> None:
        """Test step with condition function."""

        def condition(results: dict[str, Any]) -> bool:
            return "research_output" in results

        step = OrchestrationStep(
            agent_type="strategist",
            task="Strategy task",
            condition=condition,
        )

        assert step.condition is not None
        assert step.condition({"research_output": {}}) is True
        assert step.condition({}) is False


# =============================================================================
# Test: Pipeline Configuration
# =============================================================================


class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default pipeline config values."""
        config = PipelineConfig()

        assert config.autonomy_mode == AutonomyMode.CAUTIOUS
        assert config.fail_fast is True
        assert config.aggregate_checkpoints is True
        assert config.max_retries == 2
        assert config.timeout_seconds == 600

    def test_custom_config(self) -> None:
        """Test custom pipeline config values."""
        config = PipelineConfig(
            autonomy_mode=AutonomyMode.AUTONOMOUS,
            fail_fast=False,
            max_retries=5,
            timeout_seconds=300,
        )

        assert config.autonomy_mode == AutonomyMode.AUTONOMOUS
        assert config.fail_fast is False
        assert config.max_retries == 5
        assert config.timeout_seconds == 300


# =============================================================================
# Test: Pipeline Result
# =============================================================================


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_default_result(self) -> None:
        """Test default pipeline result values."""
        result = PipelineResult()

        assert result.status == PipelineStatus.PENDING
        assert result.steps_completed == []
        assert result.step_results == {}
        assert result.aggregated_checkpoints == []
        assert result.errors == []
        assert result.pipeline_id is not None

    def test_result_with_status(self) -> None:
        """Test pipeline result with custom status."""
        result = PipelineResult(status=PipelineStatus.COMPLETED)

        assert result.status == PipelineStatus.COMPLETED


# =============================================================================
# Test: Pipeline Templates
# =============================================================================


class TestPipelineTemplates:
    """Tests for built-in pipeline templates."""

    def test_get_supported_pipelines(self) -> None:
        """Test getting list of supported pipeline templates."""
        orchestrator = AgentOrchestrator()
        pipelines = orchestrator.get_supported_pipelines()

        assert "research_to_strategy" in pipelines
        assert "strategy_to_draft" in pipelines
        assert "full_pipeline" in pipelines

    def test_get_pipeline_template(self) -> None:
        """Test getting a specific pipeline template."""
        orchestrator = AgentOrchestrator()
        template = orchestrator.get_pipeline_template("research_to_strategy")

        assert len(template) == 2
        assert template[0].agent_type == "researcher"
        assert template[1].agent_type == "strategist"

    def test_get_unknown_pipeline_raises_error(self) -> None:
        """Test getting unknown pipeline raises ValueError."""
        orchestrator = AgentOrchestrator()

        with pytest.raises(ValueError) as exc_info:
            orchestrator.get_pipeline_template("nonexistent")

        assert "Unknown pipeline: nonexistent" in str(exc_info.value)


# =============================================================================
# Test: Pipeline History
# =============================================================================


class TestPipelineHistory:
    """Tests for pipeline history management."""

    def test_initial_history_empty(self) -> None:
        """Test that pipeline history starts empty."""
        orchestrator = AgentOrchestrator()

        assert orchestrator.get_pipeline_history() == []
        assert orchestrator.get_latest_result() is None

    def test_clear_history(self) -> None:
        """Test clearing pipeline history."""
        orchestrator = AgentOrchestrator()

        # Manually add to history for testing
        orchestrator._pipeline_history.append(PipelineResult())
        assert len(orchestrator.get_pipeline_history()) == 1

        orchestrator.clear_history()

        assert orchestrator.get_pipeline_history() == []
        assert orchestrator.step_results == {}


# =============================================================================
# Test: Input Resolution
# =============================================================================


class TestInputResolution:
    """Tests for input mapping resolution."""

    def test_resolve_simple_mapping(self) -> None:
        """Test resolving simple input mapping."""
        orchestrator = AgentOrchestrator()

        # Create mock result
        mock_result = MagicMock()
        mock_result.deliverable = {"findings": ["finding1", "finding2"]}

        step_results: dict[str, Any] = {"research_output": mock_result}
        mapping = {"research": "research_output.findings"}

        resolved = orchestrator._resolve_input_mapping(mapping, step_results)

        assert resolved["research"] == ["finding1", "finding2"]

    def test_resolve_missing_step(self) -> None:
        """Test resolving mapping with missing step."""
        orchestrator = AgentOrchestrator()

        step_results: dict[str, Any] = {}
        mapping = {"research": "nonexistent.findings"}

        resolved = orchestrator._resolve_input_mapping(mapping, step_results)

        assert "research" not in resolved  # Should not include missing


# =============================================================================
# Test: Orchestrator String Representation
# =============================================================================


class TestOrchestratorRepr:
    """Tests for orchestrator string representation."""

    def test_repr(self) -> None:
        """Test __repr__ method."""
        orchestrator = AgentOrchestrator(autonomy_mode=AutonomyMode.AUTONOMOUS)

        repr_str = repr(orchestrator)

        assert "AgentOrchestrator" in repr_str
        assert "mode=autonomous" in repr_str
        assert "version=2.0.0" in repr_str


# =============================================================================
# Test: Integration with Command Agents
# =============================================================================


class TestCommandAgentIntegration:
    """Integration tests for command agent support in orchestrator."""

    def test_orchestrator_lists_command_agents(self) -> None:
        """Test that orchestrator lists command agents from registry."""
        orchestrator = AgentOrchestrator()

        agent_types = orchestrator.AGENT_TYPES
        python_agents = {"researcher", "strategist", "drafter"}
        command_agents = set(agent_types) - python_agents

        # Should have discovered some command agents
        assert len(agent_types) >= 3  # At minimum Python agents
        # If command files exist, they should be discovered
        if len(agent_types) > 3:
            assert len(command_agents) > 0

    def test_orchestrator_can_create_mixed_pipeline(self) -> None:
        """Test creating a pipeline with both Python and command agents."""
        orchestrator = AgentOrchestrator()

        # Get available command agents
        command_agents = [
            a for a in orchestrator.AGENT_TYPES if a not in ["researcher", "strategist", "drafter"]
        ]

        if command_agents:
            # Create mixed pipeline
            steps = [
                OrchestrationStep(
                    agent_type="researcher",
                    task="Research legal precedents",
                    output_key="research_output",
                ),
                OrchestrationStep(
                    agent_type=command_agents[0],  # Command agent
                    task="Analyze findings",
                    input_mapping={"research": "research_output"},
                    output_key="analysis_output",
                ),
            ]

            # Verify steps are valid
            assert len(steps) == 2
            assert steps[0].agent_type == "researcher"
            assert steps[1].agent_type == command_agents[0]

    def test_command_agent_preserves_context(self, sample_case_context: CaseContext) -> None:
        """Test that command agents receive case context."""
        orchestrator = AgentOrchestrator(
            autonomy_mode=AutonomyMode.AUTONOMOUS,
            case_context=sample_case_context,
        )

        # Get any available command agent
        command_agents = [
            a for a in orchestrator.AGENT_TYPES if a not in ["researcher", "strategist", "drafter"]
        ]

        if command_agents:
            agent = orchestrator._get_agent(command_agents[0])
            assert isinstance(agent, CommandAgentAdapter)
            assert agent.case_context == sample_case_context
            assert agent.autonomy_mode == AutonomyMode.AUTONOMOUS
