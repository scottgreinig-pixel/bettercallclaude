"""
Unit tests for CommandAgentAdapter.

Tests the command file parsing, execution bridge, and adapter functionality
for wrapping command-based agents to work with the orchestrator.
"""

import tempfile
from pathlib import Path

import pytest

from src.agents.base import AgentOutcome, AutonomyMode, CaseContext
from src.agents.command_adapter import (
    CommandAgentAdapter,
    CommandParser,
    ExecutionBridge,
    ExecutionContext,
    ParsedCommand,
    create_command_adapter,
    execute_command_agent,
)
from src.agents.registry import AgentCategory, AgentDescriptor

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_command_content() -> str:
    """Sample command file content for testing."""
    return """# /agent:test - Test Agent

**Activates the Test Agent for testing purposes.**

---

## Framework Activation

**BetterCallClaude Agent Framework: ACTIVE**
**Agent**: Test Specialist
**Version**: 1.2.3
**Domain**: Testing, validation, quality assurance

---

## What This Agent Does

When you use `/agent:test`, you activate specialized testing expertise:

- **Unit Testing**: Write and run unit tests
- **Integration Testing**: Test component interactions
- **Validation**: Verify correctness

---

## Autonomy Modes

### Cautious Mode (Default)
```yaml
behavior: Confirms each test before execution
use_case: Production testing, critical systems
activation: /agent:test --mode cautious
```

### Balanced Mode
```yaml
behavior: Batch tests, confirms only failures
use_case: Development testing, CI/CD
activation: /agent:test --mode balanced
```

### Autonomous Mode
```yaml
behavior: Full test suite with summary report
use_case: Automated testing, regression suites
activation: /agent:test --mode autonomous
```

---

## Test Workflow

```
1. DISCOVER
   - Find test files
   - Identify test functions
   - Detect test frameworks

2. EXECUTE
   - Run discovered tests
   - Capture results
   - Record timing

3. ANALYZE
   - Identify failures
   - Check coverage
   - Find patterns

4. REPORT
   - Generate summary
   - Provide recommendations
   - Create documentation
```

---

## Usage Examples

### Run All Tests
```
/agent:test run --all
```

### Test Specific Module
```
/agent:test run @module.py --verbose
```

### Coverage Analysis
```
/agent:test coverage --threshold 80
```

---

## Output Format: Test Report

```markdown
## Test Results

### Summary
- Total Tests: 50
- Passed: 48
- Failed: 2
- Coverage: 85%

### Failed Tests
- test_module.py::test_function - AssertionError
- test_other.py::test_edge_case - TimeoutError
```

---

## Configuration Options

```yaml
test_config:
  framework: pytest
  timeout: 60
  coverage_threshold: 80
  parallel: true
```

---

## Integration with Other Agents

### With Researcher Agent
```
/agent:researcher --test-validation
→ Validates research with tests
```

### With Drafter Agent
```
/agent:drafter --test-docs
→ Generates test documentation
```

---

**Test Agent is now ready. Provide test commands or files to analyze.**
"""


@pytest.fixture
def simple_command_content() -> str:
    """Minimal command file content."""
    return """# /agent:simple - Simple Agent

**A simple test agent.**

**Agent**: Simple Agent
**Version**: 1.0.0
**Domain**: general

## What This Agent Does

Basic functionality for testing.
"""


@pytest.fixture
def temp_commands_dir(sample_command_content: str) -> tempfile.TemporaryDirectory:
    """Create a temporary directory with command files."""
    temp_dir = tempfile.TemporaryDirectory()
    commands_path = Path(temp_dir.name)

    # Write sample command files
    (commands_path / "agent:test.md").write_text(sample_command_content)

    return temp_dir


@pytest.fixture
def sample_descriptor() -> AgentDescriptor:
    """Create a sample agent descriptor without command_path (requires parsed_command)."""
    return AgentDescriptor(
        agent_id="agent_test",
        name="Test Agent",
        version="1.0.0",
        description="Test agent for unit testing",
        agent_type="command",
        category=AgentCategory.SPECIALIZED,
        command_path=None,  # No path - tests must provide parsed_command
        command_name="/agent:test",
    )


@pytest.fixture
def sample_case_context() -> CaseContext:
    """Create a sample case context."""
    return CaseContext(
        case_id="TEST-001",
        title="Test Case",
        case_type="testing",
        jurisdiction_federal=True,
        jurisdiction_cantons=["ZH"],
        languages=["DE"],
    )


# =============================================================================
# CommandParser Tests
# =============================================================================


class TestCommandParser:
    """Tests for CommandParser class."""

    def test_parse_content_extracts_name(self, sample_command_content: str) -> None:
        """Test that parser extracts command name."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert result.name == "/agent:test"

    def test_parse_content_extracts_title(self, sample_command_content: str) -> None:
        """Test that parser extracts title."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert result.title == "Test Agent"

    def test_parse_content_extracts_version(self, sample_command_content: str) -> None:
        """Test that parser extracts version."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert result.version == "1.2.3"

    def test_parse_content_extracts_domain(self, sample_command_content: str) -> None:
        """Test that parser extracts domain."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert "Testing" in result.domain
        assert "validation" in result.domain
        assert "quality assurance" in result.domain

    def test_parse_content_extracts_agent_type(self, sample_command_content: str) -> None:
        """Test that parser extracts agent type."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert result.agent_type == "Test Specialist"

    def test_parse_content_extracts_workflow_steps(self, sample_command_content: str) -> None:
        """Test that parser extracts workflow steps."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert len(result.workflow_steps) == 4
        assert result.workflow_steps[0]["name"] == "DISCOVER"
        assert result.workflow_steps[1]["name"] == "EXECUTE"
        assert result.workflow_steps[2]["name"] == "ANALYZE"
        assert result.workflow_steps[3]["name"] == "REPORT"

    def test_parse_content_extracts_workflow_substeps(self, sample_command_content: str) -> None:
        """Test that parser extracts workflow sub-steps."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        # DISCOVER step should have 3 sub-steps
        discover_step = result.workflow_steps[0]
        assert len(discover_step.get("sub_steps", [])) == 3
        assert "Find test files" in discover_step["sub_steps"]

    def test_parse_content_extracts_autonomy_modes(self, sample_command_content: str) -> None:
        """Test that parser extracts autonomy modes."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert "cautious" in result.autonomy_modes
        assert "balanced" in result.autonomy_modes
        assert "autonomous" in result.autonomy_modes

        assert result.autonomy_modes["cautious"]["behavior"] is not None

    def test_parse_content_extracts_usage_examples(self, sample_command_content: str) -> None:
        """Test that parser extracts usage examples."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert len(result.usage_examples) >= 1

    def test_parse_content_extracts_config_options(self, sample_command_content: str) -> None:
        """Test that parser extracts configuration options."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert "test_config" in result.config_options

    def test_parse_content_extracts_integrations(self, sample_command_content: str) -> None:
        """Test that parser extracts integrations."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert "researcher" in result.integrations
        assert "drafter" in result.integrations

    def test_parse_content_extracts_output_format(self, sample_command_content: str) -> None:
        """Test that parser extracts output format template."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert result.output_format is not None
        assert "Test Results" in result.output_format

    def test_parse_content_stores_raw_content(self, sample_command_content: str) -> None:
        """Test that parser stores raw content."""
        result = CommandParser.parse_content(sample_command_content, "agent:test")

        assert result.raw_content == sample_command_content

    def test_parse_simple_command(self, simple_command_content: str) -> None:
        """Test parsing a minimal command file."""
        result = CommandParser.parse_content(simple_command_content, "agent:simple")

        assert result.name == "/agent:simple"
        assert result.version == "1.0.0"
        assert result.domain == "general"

    def test_parse_file(self, temp_commands_dir: tempfile.TemporaryDirectory) -> None:
        """Test parsing a command file from disk."""
        file_path = Path(temp_commands_dir.name) / "agent:test.md"
        result = CommandParser.parse(file_path)

        assert result.name == "/agent:test"
        assert result.version == "1.2.3"


class TestParsedCommand:
    """Tests for ParsedCommand dataclass."""

    def test_parsed_command_defaults(self) -> None:
        """Test default values for ParsedCommand."""
        cmd = ParsedCommand(
            name="/agent:test",
            title="Test",
            description="Test command",
            version="1.0.0",
            domain="testing",
            agent_type="Test Agent",
        )

        assert cmd.workflow_steps == []
        assert cmd.output_format is None
        assert cmd.autonomy_modes == {}
        assert cmd.usage_examples == []
        assert cmd.config_options == {}
        assert cmd.integrations == []
        assert cmd.raw_content == ""


# =============================================================================
# ExecutionBridge Tests
# =============================================================================


class TestExecutionBridge:
    """Tests for ExecutionBridge class."""

    def test_execution_bridge_initialization(self, sample_command_content: str) -> None:
        """Test ExecutionBridge initialization."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        bridge = ExecutionBridge(parsed)

        assert bridge.command == parsed

    @pytest.mark.asyncio
    async def test_execute_returns_success(self, sample_command_content: str) -> None:
        """Test successful execution."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        bridge = ExecutionBridge(parsed)

        result = await bridge.execute(
            task="Run tests",
            parameters={},
            autonomy_mode=AutonomyMode.BALANCED,
        )

        assert result["success"] is True
        assert "result" in result
        assert result["steps_completed"] == 4  # 4 workflow steps

    @pytest.mark.asyncio
    async def test_execute_includes_execution_time(self, sample_command_content: str) -> None:
        """Test that execution time is recorded."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        bridge = ExecutionBridge(parsed)

        result = await bridge.execute(
            task="Run tests",
            parameters={},
            autonomy_mode=AutonomyMode.BALANCED,
        )

        assert "execution_time_ms" in result
        assert result["execution_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_execute_with_case_context(
        self, sample_command_content: str, sample_case_context: CaseContext
    ) -> None:
        """Test execution with case context."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        bridge = ExecutionBridge(parsed)

        result = await bridge.execute(
            task="Run tests",
            parameters={},
            autonomy_mode=AutonomyMode.BALANCED,
            case_context=sample_case_context,
        )

        assert result["success"] is True
        assert result["result"]["case_id"] == "TEST-001"

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, simple_command_content: str) -> None:
        """Test executing a command without workflow steps."""
        parsed = CommandParser.parse_content(simple_command_content, "agent:simple")
        bridge = ExecutionBridge(parsed)

        result = await bridge.execute(
            task="Do something",
            parameters={},
            autonomy_mode=AutonomyMode.AUTONOMOUS,
        )

        assert result["success"] is True
        assert result["steps_completed"] == 1  # Simple execution


class TestExecutionContext:
    """Tests for ExecutionContext dataclass."""

    def test_execution_context_defaults(self, sample_command_content: str) -> None:
        """Test default values for ExecutionContext."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")

        ctx = ExecutionContext(
            task="Test task",
            parameters={},
            autonomy_mode=AutonomyMode.BALANCED,
            case_context=None,
            parsed_command=parsed,
        )

        assert ctx.current_step == 0
        assert ctx.step_results == []
        assert ctx.errors == []


# =============================================================================
# CommandAgentAdapter Tests
# =============================================================================


class TestCommandAgentAdapter:
    """Tests for CommandAgentAdapter class."""

    def test_adapter_initialization_with_descriptor(
        self, sample_descriptor: AgentDescriptor
    ) -> None:
        """Test adapter initialization with descriptor."""
        adapter = CommandAgentAdapter(descriptor=sample_descriptor)

        assert adapter.agent_id == "agent_test"
        assert adapter.agent_version == "1.0.0"

    def test_adapter_agent_id(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test agent_id property."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        assert adapter.agent_id == "agent_test"

    def test_adapter_agent_version(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test agent_version property."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        assert adapter.agent_version == "1.0.0"

    def test_adapter_descriptor_property(self, sample_descriptor: AgentDescriptor) -> None:
        """Test descriptor property."""
        adapter = CommandAgentAdapter(descriptor=sample_descriptor)

        assert adapter.descriptor == sample_descriptor

    def test_adapter_parsed_command_property(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test parsed_command property."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        assert adapter.parsed_command == parsed

    def test_adapter_workflow_steps_property(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test workflow_steps property."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        assert len(adapter.workflow_steps) == 4

    def test_adapter_supported_autonomy_modes(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test supported_autonomy_modes property."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        modes = adapter.supported_autonomy_modes
        assert AutonomyMode.CAUTIOUS in modes
        assert AutonomyMode.BALANCED in modes
        assert AutonomyMode.AUTONOMOUS in modes

    @pytest.mark.asyncio
    async def test_adapter_execute_success(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test successful execution through adapter."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        result = await adapter.execute("Run all tests")

        assert result.success is True
        assert result.outcome == AgentOutcome.SUCCESS
        assert result.deliverable is not None

    @pytest.mark.asyncio
    async def test_adapter_execute_creates_audit_log(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test that execution creates audit log."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        result = await adapter.execute("Run tests")

        assert result.audit_log is not None
        assert result.audit_log.agent_id == "agent_test"
        assert len(result.audit_log.actions) >= 2  # Start and complete actions

    @pytest.mark.asyncio
    async def test_adapter_execute_with_case_context(
        self,
        sample_descriptor: AgentDescriptor,
        sample_command_content: str,
        sample_case_context: CaseContext,
    ) -> None:
        """Test execution updates case context."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(
            descriptor=sample_descriptor,
            parsed_command=parsed,
            case_context=sample_case_context,
        )

        await adapter.execute("Run tests")

        assert "agent_test" in sample_case_context.agent_history

    @pytest.mark.asyncio
    async def test_adapter_execute_records_execution_time(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test that execution time is recorded."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        result = await adapter.execute("Run tests")

        assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_adapter_validate_task(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test task validation."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        is_valid, reason = await adapter.validate_task("Run validation tests")

        assert is_valid is True
        assert "validation" in reason.lower() or "match" in reason.lower()

    def test_adapter_get_capabilities(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test get_capabilities method."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        capabilities = adapter.get_capabilities()

        assert len(capabilities) > 0
        # Should include domain items and workflow steps
        assert any("Testing" in c or "DISCOVER" in c for c in capabilities)

    def test_adapter_get_integration_points(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test get_integration_points method."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        integrations = adapter.get_integration_points()

        assert "researcher" in integrations
        assert "drafter" in integrations


class TestCommandAgentAdapterFactories:
    """Tests for CommandAgentAdapter factory methods."""

    def test_from_descriptor(self, sample_descriptor: AgentDescriptor) -> None:
        """Test from_descriptor factory method."""
        adapter = CommandAgentAdapter.from_descriptor(
            descriptor=sample_descriptor,
            autonomy_mode=AutonomyMode.CAUTIOUS,
        )

        assert adapter.agent_id == "agent_test"
        assert adapter.autonomy_mode == AutonomyMode.CAUTIOUS

    def test_from_command_file(self, temp_commands_dir: tempfile.TemporaryDirectory) -> None:
        """Test from_command_file factory method."""
        file_path = Path(temp_commands_dir.name) / "agent:test.md"
        adapter = CommandAgentAdapter.from_command_file(file_path)

        assert adapter.agent_id == "agent_test"
        assert adapter.agent_version == "1.2.3"

    def test_from_command_file_with_options(
        self,
        temp_commands_dir: tempfile.TemporaryDirectory,
        sample_case_context: CaseContext,
    ) -> None:
        """Test from_command_file with all options."""
        file_path = Path(temp_commands_dir.name) / "agent:test.md"
        adapter = CommandAgentAdapter.from_command_file(
            file_path,
            autonomy_mode=AutonomyMode.AUTONOMOUS,
            case_context=sample_case_context,
            user_id="test_user",
            firm_id="test_firm",
        )

        assert adapter.autonomy_mode == AutonomyMode.AUTONOMOUS
        assert adapter.case_context == sample_case_context
        assert adapter.user_id == "test_user"
        assert adapter.firm_id == "test_firm"


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestFactoryFunctions:
    """Tests for module-level factory functions."""

    def test_create_command_adapter(self, temp_commands_dir: tempfile.TemporaryDirectory) -> None:
        """Test create_command_adapter function."""
        adapter = create_command_adapter(
            name="test",
            commands_dir=Path(temp_commands_dir.name),
        )

        assert adapter is not None
        assert "test" in adapter.agent_id

    def test_create_command_adapter_not_found(
        self, temp_commands_dir: tempfile.TemporaryDirectory
    ) -> None:
        """Test create_command_adapter returns None for missing file."""
        adapter = create_command_adapter(
            name="nonexistent",
            commands_dir=Path(temp_commands_dir.name),
        )

        assert adapter is None

    @pytest.mark.asyncio
    async def test_execute_command_agent(
        self, temp_commands_dir: tempfile.TemporaryDirectory
    ) -> None:
        """Test execute_command_agent function."""
        result = await execute_command_agent(
            name="test",
            task="Run all tests",
            commands_dir=Path(temp_commands_dir.name),
        )

        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_command_agent_not_found(
        self, temp_commands_dir: tempfile.TemporaryDirectory
    ) -> None:
        """Test execute_command_agent returns None for missing agent."""
        result = await execute_command_agent(
            name="nonexistent",
            task="Do something",
            commands_dir=Path(temp_commands_dir.name),
        )

        assert result is None


# =============================================================================
# Integration Tests
# =============================================================================


class TestCommandAdapterIntegration:
    """Integration tests for command adapter functionality."""

    @pytest.mark.asyncio
    async def test_full_execution_workflow(
        self, temp_commands_dir: tempfile.TemporaryDirectory
    ) -> None:
        """Test complete execution workflow from file to result."""
        # Create adapter from file
        file_path = Path(temp_commands_dir.name) / "agent:test.md"
        adapter = CommandAgentAdapter.from_command_file(file_path)

        # Validate task
        is_valid, _ = await adapter.validate_task("Run unit tests")
        assert is_valid

        # Execute
        result = await adapter.execute("Run unit tests", verbose=True)

        # Verify result
        assert result.success is True
        assert result.outcome == AgentOutcome.SUCCESS
        assert result.deliverable is not None
        assert result.audit_log is not None

        # Verify deliverable structure
        deliverable = result.deliverable
        assert "command" in deliverable
        assert "workflow_steps" in deliverable
        assert deliverable["total_steps"] == 4

    @pytest.mark.asyncio
    async def test_adapter_checkpoint_creation(
        self, sample_descriptor: AgentDescriptor, sample_command_content: str
    ) -> None:
        """Test that adapter creates checkpoints during execution."""
        parsed = CommandParser.parse_content(sample_command_content, "agent:test")
        adapter = CommandAgentAdapter(descriptor=sample_descriptor, parsed_command=parsed)

        result = await adapter.execute("Run tests")

        # Check that checkpoints were created
        assert len(result.audit_log.checkpoints) >= 1

    @pytest.mark.asyncio
    async def test_adapter_with_all_autonomy_modes(
        self, temp_commands_dir: tempfile.TemporaryDirectory
    ) -> None:
        """Test adapter with different autonomy modes."""
        file_path = Path(temp_commands_dir.name) / "agent:test.md"

        for mode in [AutonomyMode.CAUTIOUS, AutonomyMode.BALANCED, AutonomyMode.AUTONOMOUS]:
            adapter = CommandAgentAdapter.from_command_file(file_path, autonomy_mode=mode)
            result = await adapter.execute("Run tests")

            assert result.success is True
            assert result.deliverable is not None
            assert result.deliverable["autonomy_mode"] == mode.value

    @pytest.mark.asyncio
    async def test_adapter_error_handling_no_bridge(
        self, sample_descriptor: AgentDescriptor
    ) -> None:
        """Test error handling when execution bridge is missing."""
        # Create adapter without parsed command (no bridge)
        adapter = CommandAgentAdapter(descriptor=sample_descriptor)

        result = await adapter.execute("Run tests")

        assert result.success is False
        assert result.outcome == AgentOutcome.FAILED
        assert result.error_message is not None
        assert "execution bridge" in result.error_message.lower()
