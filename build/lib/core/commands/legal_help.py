"""
Legal help command for BetterCallClaude v2.0

This module implements the /legal:help command for displaying available
commands and their usage information.
"""

from typing import Any

from .base import BaseCommand, CommandCategory, CommandMetadata


class LegalHelpCommand(BaseCommand):
    """
    Display help information for available commands

    Shows categorized list of commands with descriptions and usage examples.
    Can display general help or detailed help for specific commands.

    Example:
        /legal:help                    # Show all commands
        /legal:help --category=research  # Show research commands only
        /legal:help --command=legal:research  # Detailed help for specific command
    """

    def __init__(self) -> None:
        """Initialize legal help command with metadata and arguments"""
        metadata = CommandMetadata(
            name="legal:help",
            category=CommandCategory.SYSTEM,
            description="Display available commands and usage information",
            help_text=("/legal:help [--category=<cat>] [--command=<name>] [--verbose]"),
            auto_personas=[],  # No persona activation for help
            mcp_servers=[],  # No MCP servers needed for help
            requires_auth=False,
        )
        super().__init__(metadata)

        # Define command arguments
        self.add_argument(
            name="category",
            arg_type=str,
            required=False,
            default=None,
            help_text=(
                "Filter by category: research, drafting, analysis, "
                "case_strategy, compliance, document, swiss_law, system"
            ),
        )

        self.add_argument(
            name="command",
            arg_type=str,
            required=False,
            default=None,
            help_text="Show detailed help for specific command",
        )

        self.add_argument(
            name="verbose",
            arg_type=bool,
            required=False,
            default=False,
            help_text="Show detailed information including arguments and examples",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute help command

        Args:
            args: Validated command arguments containing:
                - category: Optional category filter
                - command: Optional specific command name
                - verbose: Show detailed information

        Returns:
            Dict containing:
                - success: bool
                - help_text: Formatted help text
                - commands: List of commands (if listing)
                - metadata: Help generation metadata

        Note:
            This command requires access to the CommandRegistry instance
            to list available commands. The registry will be injected by
            the CLI framework during execution.
        """
        category_filter = args.get("category")
        command_name = args.get("command")
        verbose = args.get("verbose", False)

        # TODO: Integrate with CommandRegistry in CLI framework
        # For now, return placeholder help text
        if command_name:
            return self._generate_command_help(command_name, verbose)
        else:
            return self._generate_general_help(category_filter, verbose)

    def _generate_command_help(self, command_name: str, verbose: bool) -> dict[str, Any]:
        """
        Generate detailed help for specific command

        Args:
            command_name: Name of command to get help for
            verbose: Include detailed argument information

        Returns:
            Dict with command-specific help information
        """
        # TODO: Get actual command from registry
        # Placeholder implementation
        help_text = f"""
Command: /{command_name}

Detailed help for this command will be available once the CommandRegistry
integration is complete.

Usage:
  /{command_name} <args>

For now, use /legal:help to see all available commands.
"""
        return {
            "success": True,
            "help_text": help_text.strip(),
            "command": command_name,
            "metadata": {"verbose": verbose},
        }

    def _generate_general_help(self, category_filter: str | None, verbose: bool) -> dict[str, Any]:
        """
        Generate general help listing all commands

        Args:
            category_filter: Optional category to filter by
            verbose: Include detailed information

        Returns:
            Dict with categorized command listing
        """
        help_text = """
BetterCallClaude v2.0 - Swiss Legal Intelligence CLI

Available Commands:
"""

        # TODO: Get actual commands from registry
        # Placeholder implementation showing expected categories
        categories = {
            "RESEARCH": [
                {
                    "name": "legal:research",
                    "description": "Search Swiss legal sources for precedents",
                }
            ],
            "SYSTEM": [{"name": "legal:help", "description": "Display this help message"}],
        }

        if category_filter:
            help_text += f"\nFiltered by category: {category_filter}\n"

        for category, commands in categories.items():
            if category_filter and category.lower() != category_filter.lower():
                continue

            help_text += f"\n{category}:\n"
            for cmd in commands:
                help_text += f"  /{cmd['name']:<25} {cmd['description']}\n"

        help_text += """
Usage:
  /legal:help --command=<name>    Show detailed help for specific command
  /legal:help --category=<cat>    Filter by category
  /legal:help --verbose           Show detailed information

For more information, see docs/onboarding/SETUP.md
"""

        return {
            "success": True,
            "help_text": help_text.strip(),
            "categories": list(categories.keys()),
            "metadata": {"category_filter": category_filter, "verbose": verbose},
        }
