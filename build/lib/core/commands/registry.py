"""
Command registry for auto-discovery and routing

This module provides the CommandRegistry class that:
- Auto-discovers commands from the commands package
- Registers commands with metadata
- Routes command execution
- Provides command lookup and help
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any

from .base import BaseCommand, CommandCategory


class CommandRegistry:
    """
    Registry for command auto-discovery and management

    The CommandRegistry automatically discovers all BaseCommand subclasses
    in the commands package and provides routing and lookup functionality.

    Example:
        registry = CommandRegistry()
        registry.discover_commands()

        # Execute command
        result = await registry.execute("legal:research", {"query": "BGE precedent"})

        # Get command help
        help_text = registry.get_command_help("legal:research")

        # List all commands
        commands = registry.list_commands(category=CommandCategory.RESEARCH)
    """

    def __init__(self) -> None:
        """Initialize empty command registry"""
        self._commands: dict[str, BaseCommand] = {}
        self._aliases: dict[str, str] = {}

    def register(self, command: BaseCommand, aliases: list[str] | None = None) -> None:
        """
        Register a command instance

        Args:
            command: Command instance to register
            aliases: Optional list of command aliases

        Raises:
            ValueError: If command name already registered
        """
        name = command.metadata.name

        if name in self._commands:
            raise ValueError(f"Command '{name}' is already registered")

        self._commands[name] = command

        # Register aliases
        if aliases:
            for alias in aliases:
                if alias in self._aliases:
                    raise ValueError(f"Alias '{alias}' already registered")
                self._aliases[alias] = name

    def discover_commands(self, package_path: Path | None = None) -> int:
        """
        Auto-discover and register all commands in package

        Scans the commands package for all BaseCommand subclasses and
        automatically registers them.

        Args:
            package_path: Optional path to commands package
                         (defaults to current package)

        Returns:
            Number of commands discovered and registered
        """
        if package_path is None:
            # Use current package directory
            package_path = Path(__file__).parent

        discovered_count = 0

        # Iterate through all Python files in package
        for module_info in pkgutil.iter_modules([str(package_path)]):
            if module_info.name.startswith("_") or module_info.name in [
                "base",
                "registry",
            ]:
                continue

            try:
                # Import module
                module_name = f"src.core.commands.{module_info.name}"
                module = importlib.import_module(module_name)

                # Find BaseCommand subclasses
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BaseCommand)
                        and obj is not BaseCommand
                        and not inspect.isabstract(obj)
                    ):
                        # Instantiate and register command
                        # Each concrete command implements __init__() with no args
                        command_instance = obj()  # type: ignore[call-arg]
                        self.register(command_instance)
                        discovered_count += 1

            except Exception as e:
                # Log error but continue discovery
                print(f"Warning: Failed to load module {module_info.name}: {e}")
                continue

        return discovered_count

    async def execute(
        self, command_name: str, args: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute a registered command

        Args:
            command_name: Command name or alias
            args: Command arguments

        Returns:
            Command execution result

        Raises:
            ValueError: If command not found or arguments invalid
        """
        if args is None:
            args = {}

        # Resolve alias if necessary
        if command_name in self._aliases:
            command_name = self._aliases[command_name]

        # Get command
        command = self._commands.get(command_name)
        if command is None:
            raise ValueError(
                f"Command '{command_name}' not found. "
                f"Use /legal:help to list available commands."
            )

        # Validate arguments
        is_valid, error_msg = command.validate_arguments(args)
        if not is_valid:
            raise ValueError(f"Invalid arguments: {error_msg}")

        # Execute command
        try:
            result = await command.execute(args)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command_name,
            }

    def get_command(self, command_name: str) -> BaseCommand | None:
        """
        Get command instance by name or alias

        Args:
            command_name: Command name or alias

        Returns:
            Command instance or None if not found
        """
        # Resolve alias
        if command_name in self._aliases:
            command_name = self._aliases[command_name]

        return self._commands.get(command_name)

    def get_command_help(self, command_name: str) -> str | None:
        """
        Get help text for specific command

        Args:
            command_name: Command name or alias

        Returns:
            Formatted help text or None if command not found
        """
        command = self.get_command(command_name)
        if command is None:
            return None

        return command.get_help()

    def list_commands(self, category: CommandCategory | None = None) -> list[dict[str, str]]:
        """
        List all registered commands

        Args:
            category: Optional filter by category

        Returns:
            List of command metadata dicts
        """
        commands = []

        for name, command in sorted(self._commands.items()):
            if category is None or command.metadata.category == category:
                commands.append(
                    {
                        "name": name,
                        "category": command.metadata.category.value,
                        "description": command.metadata.description,
                    }
                )

        return commands

    def list_categories(self) -> list[str]:
        """
        Get list of all command categories in use

        Returns:
            List of category names
        """
        categories = set()
        for command in self._commands.values():
            categories.add(command.metadata.category.value)

        return sorted(categories)

    def get_commands_by_category(self) -> dict[str, list[dict[str, str]]]:
        """
        Get commands organized by category

        Returns:
            Dict mapping category names to command lists
        """
        categorized = {}

        for category in CommandCategory:
            category_commands = self.list_commands(category=category)
            if category_commands:
                categorized[category.value] = category_commands

        return categorized

    def __len__(self) -> int:
        """Get number of registered commands"""
        return len(self._commands)

    def __contains__(self, command_name: str) -> bool:
        """Check if command is registered"""
        return command_name in self._commands or command_name in self._aliases

    def __repr__(self) -> str:
        """String representation of registry"""
        return (
            f"CommandRegistry(commands={len(self._commands)}, "
            f"categories={len(self.list_categories())})"
        )
