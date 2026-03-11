"""
Base command system for BetterCallClaude v2.0

This module provides the foundation for the command system, including:
- BaseCommand abstract class
- CommandMetadata for command registration
- CommandCategory enumeration
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommandCategory(Enum):
    """Command categories for organization and filtering"""

    RESEARCH = "research"
    DRAFTING = "drafting"
    ANALYSIS = "analysis"
    CASE_STRATEGY = "case_strategy"
    COMPLIANCE = "compliance"
    DOCUMENT = "document"
    SWISS_LAW = "swiss_law"
    SYSTEM = "system"


@dataclass
class CommandMetadata:
    """
    Metadata for command registration and discovery

    Attributes:
        name: Command name (e.g., "legal:research", "swiss:federal")
        category: CommandCategory for organization
        description: Short description of command purpose
        help_text: Detailed help text with usage examples
        auto_personas: List of persona IDs to auto-activate
        mcp_servers: List of MCP server IDs required
        requires_auth: Whether command requires authentication
    """

    name: str
    category: CommandCategory
    description: str
    help_text: str
    auto_personas: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)
    requires_auth: bool = False

    def __post_init__(self) -> None:
        """Initialize default values for optional fields"""
        # Default values are now handled by field(default_factory=list)
        pass


class CommandArgument:
    """
    Command argument specification

    Attributes:
        name: Argument name
        arg_type: Expected type (str, int, bool, list)
        required: Whether argument is required
        default: Default value if not provided
        help_text: Help text for argument
    """

    def __init__(
        self,
        name: str,
        arg_type: type,
        required: bool = False,
        default: Any = None,
        help_text: str = "",
    ):
        self.name = name
        self.arg_type = arg_type
        self.required = required
        self.default = default
        self.help_text = help_text

    def validate(self, value: Any) -> tuple[bool, str | None]:
        """
        Validate argument value

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            if self.required:
                return False, f"Argument '{self.name}' is required"
            return True, None

        # Type validation
        if not isinstance(value, self.arg_type):
            return (
                False,
                f"Argument '{self.name}' must be of type {self.arg_type.__name__}",
            )

        return True, None


class BaseCommand(ABC):
    """
    Abstract base class for all commands

    All commands must inherit from this class and implement the execute() method.

    Example:
        class LegalResearchCommand(BaseCommand):
            def __init__(self):
                metadata = CommandMetadata(
                    name="legal:research",
                    category=CommandCategory.RESEARCH,
                    description="Search legal sources",
                    help_text="Usage: /legal:research <query> [--jurisdiction=federal]",
                    auto_personas=["legal_researcher"],
                    mcp_servers=["bge_search", "entscheidsuche"]
                )
                super().__init__(metadata)

            async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
                query = args.get("query")
                # Implementation here
                return {"results": [...]}
    """

    def __init__(self, metadata: CommandMetadata):
        """
        Initialize base command

        Args:
            metadata: Command metadata for registration
        """
        self.metadata = metadata
        self.arguments: list[CommandArgument] = []

    def add_argument(
        self,
        name: str,
        arg_type: type,
        required: bool = False,
        default: Any = None,
        help_text: str = "",
    ) -> None:
        """
        Add argument specification to command

        Args:
            name: Argument name
            arg_type: Expected type
            required: Whether required
            default: Default value
            help_text: Help text
        """
        arg = CommandArgument(
            name=name,
            arg_type=arg_type,
            required=required,
            default=default,
            help_text=help_text,
        )
        self.arguments.append(arg)

    def validate_arguments(self, args: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Validate provided arguments against specifications

        Args:
            args: Arguments to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        for arg_spec in self.arguments:
            value = args.get(arg_spec.name)
            is_valid, error_msg = arg_spec.validate(value)
            if not is_valid:
                return False, error_msg

        return True, None

    @abstractmethod
    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the command with validated arguments

        Args:
            args: Command arguments (already validated)

        Returns:
            Command execution result

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def get_help(self) -> str:
        """
        Get formatted help text for command

        Returns:
            Formatted help text with arguments
        """
        help_lines = [
            f"Command: /{self.metadata.name}",
            f"Category: {self.metadata.category.value}",
            f"Description: {self.metadata.description}",
            "",
            "Usage:",
            f"  {self.metadata.help_text}",
        ]

        if self.arguments:
            help_lines.extend(["", "Arguments:"])
            for arg in self.arguments:
                required_str = "(required)" if arg.required else "(optional)"
                default_str = f" [default: {arg.default}]" if arg.default is not None else ""
                help_lines.append(
                    f"  {arg.name} ({arg.arg_type.__name__}) {required_str}{default_str}"
                )
                if arg.help_text:
                    help_lines.append(f"    {arg.help_text}")

        if self.metadata.auto_personas:
            help_lines.extend(
                ["", "Auto-activated Personas:", f"  {', '.join(self.metadata.auto_personas)}"]
            )

        if self.metadata.mcp_servers:
            help_lines.extend(
                ["", "Required MCP Servers:", f"  {', '.join(self.metadata.mcp_servers)}"]
            )

        return "\n".join(help_lines)
