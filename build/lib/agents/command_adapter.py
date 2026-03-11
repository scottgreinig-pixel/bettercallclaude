"""
BetterCallClaude Command Agent Adapter

This module provides an adapter class that wraps command-based agents (defined as
markdown files in .claude/commands/) to work with the Python-based orchestrator.

Architecture:
- CommandAgentAdapter: Inherits from AgentBase, wraps command file execution
- CommandParser: Parses markdown command files to extract metadata and workflow
- ExecutionBridge: Bridges command invocation to actual execution
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import (
    ActionType,
    AgentBase,
    AgentOutcome,
    AgentResult,
    AutonomyMode,
    CaseContext,
)
from .registry import AgentCategory, AgentDescriptor

logger = logging.getLogger(__name__)


# =============================================================================
# Command File Parser
# =============================================================================


@dataclass
class ParsedCommand:
    """Parsed content from a command file."""

    name: str
    title: str
    description: str
    version: str
    domain: str
    agent_type: str

    # Workflow information
    workflow_steps: list[dict[str, Any]] = field(default_factory=list)
    output_format: str | None = None

    # Autonomy modes
    autonomy_modes: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Usage examples
    usage_examples: list[dict[str, str]] = field(default_factory=list)

    # Configuration options
    config_options: dict[str, Any] = field(default_factory=dict)

    # Integration points
    integrations: list[str] = field(default_factory=list)

    # Raw content for execution
    raw_content: str = ""


class CommandParser:
    """
    Parses markdown command files to extract structured metadata and workflow.

    The parser extracts:
    - Agent metadata (name, version, domain)
    - Workflow steps from numbered lists
    - Autonomy mode configurations
    - Usage examples
    - Configuration options
    - Integration points
    """

    # Regex patterns for parsing
    TITLE_PATTERN = re.compile(r"^#\s+(/[\w:-]+)\s*-?\s*(.*)$", re.MULTILINE)
    VERSION_PATTERN = re.compile(r"\*\*Version\*\*:\s*([\d.]+)", re.IGNORECASE)
    DOMAIN_PATTERN = re.compile(r"\*\*Domain\*\*:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
    AGENT_PATTERN = re.compile(r"\*\*Agent\*\*:\s*(.+)$", re.MULTILINE | re.IGNORECASE)

    # Workflow parsing
    WORKFLOW_SECTION_PATTERN = re.compile(
        r"##\s+.*(?:Workflow|Process|Steps).*\n+```\n([\s\S]*?)\n```", re.IGNORECASE
    )
    NUMBERED_STEP_PATTERN = re.compile(r"(\d+)\.\s+([A-Z]+[A-Z\s]*)\n([\s\S]*?)(?=\n\d+\.|$)")

    # Autonomy mode parsing
    AUTONOMY_SECTION_PATTERN = re.compile(
        r"###\s+(Cautious|Balanced|Autonomous)\s+Mode.*?\n```yaml\n([\s\S]*?)\n```",
        re.IGNORECASE,
    )

    # Usage examples
    USAGE_EXAMPLE_PATTERN = re.compile(
        r"###\s+(?:Example\s*:?\s*)?(.+?)\n```\n(.*?)\n```", re.DOTALL | re.IGNORECASE
    )

    # Configuration parsing (matches "Configuration", "Configuration Options", etc.)
    CONFIG_SECTION_PATTERN = re.compile(
        r"##\s+Configuration(?:\s+Options?)?\s*\n+```yaml\n([\s\S]*?)\n```", re.IGNORECASE
    )

    # Integration parsing
    INTEGRATION_PATTERN = re.compile(r"/agent:(\w+)", re.IGNORECASE)

    @classmethod
    def parse(cls, file_path: Path) -> ParsedCommand:
        """
        Parse a command file and extract structured information.

        Args:
            file_path: Path to the command markdown file

        Returns:
            ParsedCommand with extracted metadata and workflow

        Raises:
            ValueError: If required fields cannot be parsed
        """
        content = file_path.read_text(encoding="utf-8")
        return cls.parse_content(content, file_path.stem)

    @classmethod
    def parse_content(cls, content: str, name: str) -> ParsedCommand:
        """
        Parse command content string.

        Args:
            content: Markdown content of the command file
            name: Name of the command (from filename)

        Returns:
            ParsedCommand with extracted metadata
        """
        # Extract title and description
        title_match = cls.TITLE_PATTERN.search(content)
        if title_match:
            command_name = title_match.group(1)
            title = title_match.group(2).strip() or command_name
        else:
            command_name = f"/{name}"
            title = name.replace(":", " ").replace("-", " ").title()

        # Extract version
        version_match = cls.VERSION_PATTERN.search(content)
        version = version_match.group(1) if version_match else "1.0.0"

        # Extract domain
        domain_match = cls.DOMAIN_PATTERN.search(content)
        domain = domain_match.group(1).strip() if domain_match else "general"

        # Extract agent type
        agent_match = cls.AGENT_PATTERN.search(content)
        agent_type = agent_match.group(1).strip() if agent_match else title

        # Extract description (first paragraph after title)
        desc_match = re.search(r"^#.*?\n+\*\*(.+?)\*\*", content, re.MULTILINE)
        if desc_match:
            description = desc_match.group(1).strip()
        else:
            # Try to get first substantial paragraph
            paragraphs = re.findall(r"\n\n([^#\*`\n].{50,}?)(?=\n\n|$)", content)
            description = paragraphs[0] if paragraphs else f"{title} agent"

        # Parse workflow steps
        workflow_steps = cls._parse_workflow(content)

        # Parse autonomy modes
        autonomy_modes = cls._parse_autonomy_modes(content)

        # Parse usage examples
        usage_examples = cls._parse_usage_examples(content)

        # Parse configuration options
        config_options = cls._parse_config(content)

        # Parse integrations
        integrations = cls._parse_integrations(content)

        # Extract output format section
        output_format = cls._extract_output_format(content)

        return ParsedCommand(
            name=command_name,
            title=title,
            description=description,
            version=version,
            domain=domain,
            agent_type=agent_type,
            workflow_steps=workflow_steps,
            output_format=output_format,
            autonomy_modes=autonomy_modes,
            usage_examples=usage_examples,
            config_options=config_options,
            integrations=integrations,
            raw_content=content,
        )

    @classmethod
    def _parse_workflow(cls, content: str) -> list[dict[str, Any]]:
        """Extract workflow steps from the command content."""
        steps = []

        workflow_match = cls.WORKFLOW_SECTION_PATTERN.search(content)
        if workflow_match:
            workflow_text = workflow_match.group(1)

            for step_match in cls.NUMBERED_STEP_PATTERN.finditer(workflow_text):
                step_num = int(step_match.group(1))
                step_name = step_match.group(2).strip()
                step_details = step_match.group(3).strip()

                # Parse sub-items
                sub_items = re.findall(r"^\s*-\s*(.+)$", step_details, re.MULTILINE)

                steps.append(
                    {
                        "number": step_num,
                        "name": step_name,
                        "description": step_details.split("\n")[0] if step_details else "",
                        "sub_steps": sub_items,
                    }
                )

        return steps

    @classmethod
    def _parse_autonomy_modes(cls, content: str) -> dict[str, dict[str, Any]]:
        """Extract autonomy mode configurations."""
        modes = {}

        for match in cls.AUTONOMY_SECTION_PATTERN.finditer(content):
            mode_name = match.group(1).lower()
            mode_yaml = match.group(2)

            # Simple YAML-like parsing
            mode_config = {}
            for line in mode_yaml.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    mode_config[key.strip()] = value.strip()

            modes[mode_name] = mode_config

        return modes

    @classmethod
    def _parse_usage_examples(cls, content: str) -> list[dict[str, str]]:
        """Extract usage examples from the content."""
        examples = []

        # Look for Usage Examples section
        usage_section = re.search(
            r"##\s+Usage Examples?\s*\n([\s\S]*?)(?=\n##\s+|$)", content, re.IGNORECASE
        )

        if usage_section:
            section_content = usage_section.group(1)

            # Find code blocks with their headings
            for match in re.finditer(
                r"###\s+(.+?)\n+```(?:\w+)?\n(.*?)\n```", section_content, re.DOTALL
            ):
                examples.append({"title": match.group(1).strip(), "code": match.group(2).strip()})

        return examples

    @classmethod
    def _parse_config(cls, content: str) -> dict[str, Any]:
        """Extract configuration options."""
        config = {}

        config_match = cls.CONFIG_SECTION_PATTERN.search(content)
        if config_match:
            yaml_content = config_match.group(1)

            # Simple YAML parsing (nested structures)
            current_section = None
            for line in yaml_content.strip().split("\n"):
                if not line.strip():
                    continue

                # Check indentation
                indent = len(line) - len(line.lstrip())

                if indent == 0 and ":" in line:
                    key = line.split(":")[0].strip()
                    value = line.split(":", 1)[1].strip() if ":" in line else ""
                    if value:
                        config[key] = value
                    else:
                        current_section = key
                        config[current_section] = {}
                elif indent > 0 and current_section and ":" in line:
                    key = line.split(":")[0].strip()
                    value = line.split(":", 1)[1].strip()
                    section = config[current_section]
                    if isinstance(section, dict):
                        section[key] = value

        return config

    @classmethod
    def _parse_integrations(cls, content: str) -> list[str]:
        """Extract integration points with other agents."""
        integrations = set()

        # Find all /agent: references
        for match in cls.INTEGRATION_PATTERN.finditer(content):
            agent_name = match.group(1).lower()
            integrations.add(agent_name)

        return list(integrations)

    @classmethod
    def _extract_output_format(cls, content: str) -> str | None:
        """Extract the output format template if present."""
        output_match = re.search(
            r"##\s+Output Format.*?\n+```(?:markdown)?\n([\s\S]*?)\n```",
            content,
            re.IGNORECASE,
        )

        if output_match:
            return output_match.group(1).strip()

        return None


# =============================================================================
# Execution Bridge
# =============================================================================


@dataclass
class ExecutionContext:
    """Context for command execution."""

    task: str
    parameters: dict[str, Any]
    autonomy_mode: AutonomyMode
    case_context: CaseContext | None
    parsed_command: ParsedCommand

    # Execution state
    current_step: int = 0
    step_results: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ExecutionBridge:
    """
    Bridges command-based agents to actual execution.

    The execution bridge:
    1. Takes a parsed command and execution context
    2. Simulates the workflow steps defined in the command file
    3. Collects results and formats output according to the template
    4. Handles errors and autonomy mode behaviors
    """

    def __init__(self, command: ParsedCommand):
        """
        Initialize the execution bridge.

        Args:
            command: Parsed command to execute
        """
        self.command = command
        self._start_time: datetime | None = None

    async def execute(
        self,
        task: str,
        parameters: dict[str, Any],
        autonomy_mode: AutonomyMode,
        case_context: CaseContext | None = None,
    ) -> dict[str, Any]:
        """
        Execute the command workflow.

        Args:
            task: Task description
            parameters: Additional parameters for execution
            autonomy_mode: Current autonomy mode
            case_context: Optional case context

        Returns:
            Execution result dictionary
        """
        self._start_time = datetime.utcnow()

        context = ExecutionContext(
            task=task,
            parameters=parameters,
            autonomy_mode=autonomy_mode,
            case_context=case_context,
            parsed_command=self.command,
        )

        try:
            # Execute workflow steps
            await self._execute_workflow(context)

            # Format output
            result = self._format_output(context)

            return {
                "success": True,
                "result": result,
                "steps_completed": len(context.step_results),
                "execution_time_ms": self._get_execution_time_ms(),
            }

        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            context.errors.append(str(e))

            return {
                "success": False,
                "error": str(e),
                "partial_results": context.step_results,
                "steps_completed": context.current_step,
                "execution_time_ms": self._get_execution_time_ms(),
            }

    async def _execute_workflow(self, context: ExecutionContext) -> None:
        """
        Execute the workflow steps defined in the command.

        Args:
            context: Execution context with state
        """
        workflow_steps = context.parsed_command.workflow_steps

        if not workflow_steps:
            # If no workflow defined, create a simple execution
            await self._execute_simple(context)
            return

        for i, step in enumerate(workflow_steps):
            context.current_step = i + 1

            logger.info(
                f"Executing step {step['number']}: {step['name']} "
                f"for {context.parsed_command.name}"
            )

            # Execute the step
            step_result = await self._execute_step(step, context)
            context.step_results.append(step_result)

            # Check for user confirmation in cautious mode
            if context.autonomy_mode == AutonomyMode.CAUTIOUS:
                # In a real implementation, this would pause for user input
                logger.debug(f"Cautious mode: Would confirm step {step['number']}")

    async def _execute_step(
        self, step: dict[str, Any], context: ExecutionContext
    ) -> dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: Step definition from workflow
            context: Execution context

        Returns:
            Step result dictionary
        """
        step_start = datetime.utcnow()

        # Simulate step execution
        # In a real implementation, this would delegate to specialized handlers
        result = {
            "step_number": step["number"],
            "step_name": step["name"],
            "status": "completed",
            "sub_steps_completed": len(step.get("sub_steps", [])),
            "duration_ms": 0,  # Will be updated
        }

        # Simulate some processing time
        await asyncio.sleep(0.01)

        step_end = datetime.utcnow()
        result["duration_ms"] = int((step_end - step_start).total_seconds() * 1000)

        return result

    async def _execute_simple(self, context: ExecutionContext) -> None:
        """
        Execute a simple command without defined workflow.

        Args:
            context: Execution context
        """
        context.step_results.append(
            {
                "step_number": 1,
                "step_name": "Execute",
                "status": "completed",
                "description": f"Executed {context.parsed_command.name}",
                "task": context.task,
            }
        )

    def _format_output(self, context: ExecutionContext) -> dict[str, Any]:
        """
        Format the execution output.

        Args:
            context: Execution context with results

        Returns:
            Formatted output dictionary
        """
        output = {
            "command": context.parsed_command.name,
            "agent": context.parsed_command.agent_type,
            "version": context.parsed_command.version,
            "task": context.task,
            "workflow_steps": context.step_results,
            "total_steps": len(context.step_results),
            "autonomy_mode": context.autonomy_mode.value,
        }

        # Add output format template if available
        if context.parsed_command.output_format:
            output["output_template"] = context.parsed_command.output_format

        # Add case context if available
        if context.case_context:
            output["case_id"] = context.case_context.case_id

        return output

    def _get_execution_time_ms(self) -> int:
        """Calculate execution time in milliseconds."""
        if self._start_time:
            return int((datetime.utcnow() - self._start_time).total_seconds() * 1000)
        return 0


# =============================================================================
# Command Agent Adapter
# =============================================================================


class CommandAgentAdapter(AgentBase):
    """
    Adapter that wraps command-based agents to work with the orchestrator.

    This adapter:
    1. Loads and parses command markdown files
    2. Implements the AgentBase interface
    3. Bridges execution through the ExecutionBridge
    4. Provides proper audit logging and checkpoint management

    Usage:
        adapter = CommandAgentAdapter.from_descriptor(descriptor)
        result = await adapter.execute("Analyze this contract")
    """

    def __init__(
        self,
        descriptor: AgentDescriptor,
        parsed_command: ParsedCommand | None = None,
        autonomy_mode: AutonomyMode = AutonomyMode.BALANCED,
        case_context: CaseContext | None = None,
        user_id: str = "anonymous",
        firm_id: str = "default",
    ):
        """
        Initialize the command agent adapter.

        Args:
            descriptor: Agent descriptor from registry
            parsed_command: Pre-parsed command (optional, will parse if not provided)
            autonomy_mode: Autonomy level for execution
            case_context: Shared case context
            user_id: User identifier
            firm_id: Firm identifier
        """
        super().__init__(
            autonomy_mode=autonomy_mode,
            case_context=case_context,
            user_id=user_id,
            firm_id=firm_id,
        )

        self._descriptor = descriptor
        self._parsed_command = parsed_command
        self._execution_bridge: ExecutionBridge | None = None

        # Load and parse command if not provided
        if self._parsed_command is None and descriptor.command_path:
            self._parsed_command = CommandParser.parse(Path(descriptor.command_path))

        # Create execution bridge
        if self._parsed_command:
            self._execution_bridge = ExecutionBridge(self._parsed_command)

    @classmethod
    def from_descriptor(
        cls,
        descriptor: AgentDescriptor,
        autonomy_mode: AutonomyMode = AutonomyMode.BALANCED,
        case_context: CaseContext | None = None,
        user_id: str = "anonymous",
        firm_id: str = "default",
    ) -> "CommandAgentAdapter":
        """
        Create an adapter from an agent descriptor.

        Args:
            descriptor: Agent descriptor from registry
            autonomy_mode: Autonomy level
            case_context: Case context
            user_id: User identifier
            firm_id: Firm identifier

        Returns:
            Configured CommandAgentAdapter
        """
        return cls(
            descriptor=descriptor,
            autonomy_mode=autonomy_mode,
            case_context=case_context,
            user_id=user_id,
            firm_id=firm_id,
        )

    @classmethod
    def from_command_file(
        cls,
        file_path: Path,
        autonomy_mode: AutonomyMode = AutonomyMode.BALANCED,
        case_context: CaseContext | None = None,
        user_id: str = "anonymous",
        firm_id: str = "default",
    ) -> "CommandAgentAdapter":
        """
        Create an adapter directly from a command file.

        Args:
            file_path: Path to the command markdown file
            autonomy_mode: Autonomy level
            case_context: Case context
            user_id: User identifier
            firm_id: Firm identifier

        Returns:
            Configured CommandAgentAdapter
        """
        parsed = CommandParser.parse(file_path)

        # Create a descriptor from parsed command
        agent_id = parsed.name.strip("/").replace(":", "_")
        descriptor = AgentDescriptor(
            agent_id=agent_id,
            name=parsed.title,
            version=parsed.version,
            description=parsed.description,
            agent_type="command",
            category=AgentCategory.SPECIALIZED,
            command_path=str(file_path),
            command_name=parsed.name,
        )

        return cls(
            descriptor=descriptor,
            parsed_command=parsed,
            autonomy_mode=autonomy_mode,
            case_context=case_context,
            user_id=user_id,
            firm_id=firm_id,
        )

    @property
    def agent_id(self) -> str:
        """Return unique identifier for this agent."""
        return self._descriptor.agent_id

    @property
    def agent_version(self) -> str:
        """Return version string for this agent."""
        return self._descriptor.version

    @property
    def descriptor(self) -> AgentDescriptor:
        """Return the agent descriptor."""
        return self._descriptor

    @property
    def parsed_command(self) -> ParsedCommand | None:
        """Return the parsed command."""
        return self._parsed_command

    @property
    def workflow_steps(self) -> list[dict[str, Any]]:
        """Return the workflow steps from the parsed command."""
        if self._parsed_command:
            return self._parsed_command.workflow_steps
        return []

    @property
    def supported_autonomy_modes(self) -> list[AutonomyMode]:
        """Return supported autonomy modes based on command definition."""
        if self._parsed_command and self._parsed_command.autonomy_modes:
            modes = []
            mode_mapping = {
                "cautious": AutonomyMode.CAUTIOUS,
                "balanced": AutonomyMode.BALANCED,
                "autonomous": AutonomyMode.AUTONOMOUS,
            }
            for mode_name in self._parsed_command.autonomy_modes:
                if mode_name in mode_mapping:
                    modes.append(mode_mapping[mode_name])
            return modes if modes else list(AutonomyMode)
        return list(AutonomyMode)

    async def execute(self, task: str, **kwargs: Any) -> AgentResult[dict[str, Any]]:
        """
        Execute the command agent's workflow.

        Args:
            task: Task description
            **kwargs: Additional parameters for execution

        Returns:
            AgentResult with execution results and audit information
        """
        self._start_time = datetime.utcnow()

        # Create checkpoint before execution
        self.create_checkpoint("pre_execution", f"Before executing {self.agent_id}")

        # Record the task
        self._record_action(
            ActionType.ANALYZE,
            f"Starting execution of {self.agent_id}",
            inputs={"task": task, **kwargs},
            outputs={},
            duration_ms=0,
        )

        try:
            if not self._execution_bridge:
                raise ValueError(f"No execution bridge available for {self.agent_id}")

            # Execute through the bridge
            result = await self._execution_bridge.execute(
                task=task,
                parameters=kwargs,
                autonomy_mode=self.autonomy_mode,
                case_context=self.case_context,
            )

            # Record completion
            execution_time_ms = result.get("execution_time_ms", 0)

            self._record_action(
                ActionType.GENERATE,
                f"Completed execution of {self.agent_id}",
                inputs={},
                outputs={"steps_completed": result.get("steps_completed", 0)},
                duration_ms=execution_time_ms,
            )

            # Record source access
            self.record_source_access(f"command:{self.agent_id}")

            # Update case context if available
            if self.case_context:
                self.case_context.agent_history.append(self.agent_id)

            # Create audit log
            outcome = AgentOutcome.SUCCESS if result.get("success") else AgentOutcome.PARTIAL
            audit_log = self._create_audit_log(outcome, [f"{self.agent_id}_result"])

            return AgentResult(
                success=result.get("success", False),
                outcome=outcome,
                deliverable=result.get("result"),
                partial_results=result.get("partial_results"),
                error_message=result.get("error"),
                audit_log=audit_log,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            logger.error(f"Command agent execution failed: {e}", exc_info=True)
            self._handle_error(e, recoverable=False)

            execution_time_ms = int((datetime.utcnow() - self._start_time).total_seconds() * 1000)

            audit_log = self._create_audit_log(AgentOutcome.FAILED, [])

            return AgentResult(
                success=False,
                outcome=AgentOutcome.FAILED,
                deliverable=None,
                partial_results=self._create_partial_result(None),
                error_message=str(e),
                audit_log=audit_log,
                execution_time_ms=execution_time_ms,
            )

    async def validate_task(self, task: str) -> tuple[bool, str]:
        """
        Validate if this agent can handle the given task.

        Args:
            task: Task description to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        if not self._parsed_command:
            return False, "Command not parsed"

        # Check if task matches agent's domain
        domain_lower = self._parsed_command.domain.lower()
        task_lower = task.lower()

        # Simple keyword matching
        domain_keywords = domain_lower.split(",")
        for keyword in domain_keywords:
            keyword = keyword.strip()
            if keyword and keyword in task_lower:
                return True, f"Task matches domain keyword: {keyword}"

        # Check against usage examples
        for example in self._parsed_command.usage_examples:
            if any(word in task_lower for word in example.get("code", "").lower().split()):
                return True, "Task matches usage example pattern"

        return True, "Task accepted (general match)"

    def get_capabilities(self) -> list[str]:
        """
        Get the list of capabilities this agent provides.

        Returns:
            List of capability descriptions
        """
        capabilities = []

        if self._parsed_command:
            # Extract from domain
            for domain in self._parsed_command.domain.split(","):
                capabilities.append(domain.strip())

            # Extract from workflow steps
            for step in self._parsed_command.workflow_steps:
                capabilities.append(step.get("name", ""))

        return [c for c in capabilities if c]

    def get_integration_points(self) -> list[str]:
        """
        Get agents this command can integrate with.

        Returns:
            List of agent names this command integrates with
        """
        if self._parsed_command:
            return self._parsed_command.integrations
        return []


# =============================================================================
# Factory Functions
# =============================================================================


def create_command_adapter(
    name: str,
    commands_dir: Path | None = None,
    autonomy_mode: AutonomyMode = AutonomyMode.BALANCED,
    case_context: CaseContext | None = None,
) -> CommandAgentAdapter | None:
    """
    Factory function to create a command adapter by name.

    Args:
        name: Agent name (e.g., "citation", "fiscal", "corporate")
        commands_dir: Directory containing command files
        autonomy_mode: Autonomy level
        case_context: Case context

    Returns:
        CommandAgentAdapter or None if not found
    """
    if commands_dir is None:
        commands_dir = Path(".claude/commands")

    # Try to find the command file
    patterns = [
        f"agent:{name}.md",
        f"agent-{name}.md",
        f"{name}.md",
    ]

    for pattern in patterns:
        file_path = commands_dir / pattern
        if file_path.exists():
            return CommandAgentAdapter.from_command_file(
                file_path=file_path,
                autonomy_mode=autonomy_mode,
                case_context=case_context,
            )

    logger.warning(f"Command file not found for agent: {name}")
    return None


async def execute_command_agent(
    name: str,
    task: str,
    commands_dir: Path | None = None,
    autonomy_mode: AutonomyMode = AutonomyMode.BALANCED,
    case_context: CaseContext | None = None,
    **kwargs: Any,
) -> AgentResult[dict[str, Any]] | None:
    """
    Convenience function to execute a command agent by name.

    Args:
        name: Agent name
        task: Task to execute
        commands_dir: Directory containing command files
        autonomy_mode: Autonomy level
        case_context: Case context
        **kwargs: Additional parameters

    Returns:
        AgentResult or None if agent not found
    """
    adapter = create_command_adapter(
        name=name,
        commands_dir=commands_dir,
        autonomy_mode=autonomy_mode,
        case_context=case_context,
    )

    if adapter:
        return await adapter.execute(task, **kwargs)

    return None
