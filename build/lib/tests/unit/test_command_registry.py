"""
Unit tests for Command Registry System

Tests the CommandRegistry, BaseCommand, and command discovery functionality.
"""

from typing import Any

import pytest

from src.core.commands import (
    BaseCommand,
    CommandArgument,
    CommandCategory,
    CommandMetadata,
    CommandRegistry,
)


class TestCommandArgument:
    """Test CommandArgument validation"""

    def test_validate_required_argument_present(self) -> None:
        """Test validation passes when required argument is provided"""
        arg = CommandArgument(name="query", arg_type=str, required=True)
        is_valid, error = arg.validate("test query")

        assert is_valid is True
        assert error is None

    def test_validate_required_argument_missing(self) -> None:
        """Test validation fails when required argument is missing"""
        arg = CommandArgument(name="query", arg_type=str, required=True)
        is_valid, error = arg.validate(None)

        assert is_valid is False
        assert error is not None and "required" in error.lower()

    def test_validate_type_checking(self) -> None:
        """Test type validation"""
        arg = CommandArgument(name="limit", arg_type=int, required=False)
        is_valid, error = arg.validate("not an int")

        assert is_valid is False
        assert error is not None and "type" in error.lower()

    def test_validate_optional_with_none(self) -> None:
        """Test optional argument accepts None"""
        arg = CommandArgument(name="limit", arg_type=int, required=False)
        is_valid, error = arg.validate(None)

        assert is_valid is True
        assert error is None


class MockCommand(BaseCommand):
    """Mock command for testing"""

    def __init__(self) -> None:
        metadata = CommandMetadata(
            name="test:mock",
            category=CommandCategory.SYSTEM,
            description="Mock command for testing",
            help_text="/test:mock <query>",
        )
        super().__init__(metadata)
        self.add_argument("query", str, required=True)

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"success": True, "query": args.get("query")}


class TestBaseCommand:
    """Test BaseCommand functionality"""

    def test_command_initialization(self) -> None:
        """Test command initializes with metadata"""
        cmd = MockCommand()

        assert cmd.metadata.name == "test:mock"
        assert cmd.metadata.category == CommandCategory.SYSTEM
        assert len(cmd.arguments) == 1

    def test_add_argument(self) -> None:
        """Test adding arguments to command"""
        cmd = MockCommand()
        cmd.add_argument("limit", int, required=False, default=10)

        assert len(cmd.arguments) == 2
        assert cmd.arguments[1].name == "limit"
        assert cmd.arguments[1].default == 10

    def test_validate_arguments_success(self) -> None:
        """Test argument validation passes with valid args"""
        cmd = MockCommand()
        args = {"query": "test"}

        is_valid, error = cmd.validate_arguments(args)

        assert is_valid is True
        assert error is None

    def test_validate_arguments_failure(self) -> None:
        """Test argument validation fails with invalid args"""
        cmd = MockCommand()
        args: dict[str, Any] = {}  # Missing required "query"

        is_valid, error = cmd.validate_arguments(args)

        assert is_valid is False
        assert error is not None

    def test_get_help(self) -> None:
        """Test help text generation"""
        cmd = MockCommand()
        help_text = cmd.get_help()

        assert "/test:mock" in help_text
        assert "Mock command" in help_text
        assert "query" in help_text


class TestCommandRegistry:
    """Test CommandRegistry functionality"""

    def test_register_command(self) -> None:
        """Test command registration"""
        registry = CommandRegistry()
        cmd = MockCommand()

        registry.register(cmd)

        assert "test:mock" in registry
        assert len(registry) == 1

    def test_register_duplicate_command(self) -> None:
        """Test registering duplicate command raises error"""
        registry = CommandRegistry()
        cmd1 = MockCommand()
        cmd2 = MockCommand()

        registry.register(cmd1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(cmd2)

    def test_register_with_alias(self) -> None:
        """Test command registration with alias"""
        registry = CommandRegistry()
        cmd = MockCommand()

        registry.register(cmd, aliases=["mock"])

        assert "test:mock" in registry
        assert "mock" in registry

    @pytest.mark.asyncio
    async def test_execute_command(self) -> None:
        """Test command execution"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd)

        result = await registry.execute("test:mock", {"query": "test"})

        assert result["success"] is True
        assert result["query"] == "test"

    @pytest.mark.asyncio
    async def test_execute_with_alias(self) -> None:
        """Test command execution via alias"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd, aliases=["mock"])

        result = await registry.execute("mock", {"query": "test"})

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_nonexistent_command(self) -> None:
        """Test executing nonexistent command raises error"""
        registry = CommandRegistry()

        with pytest.raises(ValueError, match="not found"):
            await registry.execute("nonexistent", {})

    @pytest.mark.asyncio
    async def test_execute_with_invalid_arguments(self) -> None:
        """Test execution with invalid arguments raises error"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd)

        with pytest.raises(ValueError, match="Invalid arguments"):
            await registry.execute("test:mock", {})  # Missing required "query"

    def test_get_command(self) -> None:
        """Test retrieving command by name"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd)

        retrieved = registry.get_command("test:mock")

        assert retrieved is cmd

    def test_get_command_by_alias(self) -> None:
        """Test retrieving command by alias"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd, aliases=["mock"])

        retrieved = registry.get_command("mock")

        assert retrieved is cmd

    def test_list_commands(self) -> None:
        """Test listing all commands"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd)

        commands = registry.list_commands()

        assert len(commands) == 1
        assert commands[0]["name"] == "test:mock"

    def test_list_commands_by_category(self) -> None:
        """Test filtering commands by category"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd)

        commands = registry.list_commands(category=CommandCategory.SYSTEM)

        assert len(commands) == 1

        commands = registry.list_commands(category=CommandCategory.RESEARCH)

        assert len(commands) == 0

    def test_get_commands_by_category(self) -> None:
        """Test grouping commands by category"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd)

        categorized = registry.get_commands_by_category()

        assert CommandCategory.SYSTEM.value in categorized
        assert len(categorized[CommandCategory.SYSTEM.value]) == 1

    def test_register_duplicate_alias_raises(self) -> None:
        """Test registering duplicate alias raises error"""
        registry = CommandRegistry()
        cmd1 = MockCommand()

        class AnotherMockCommand(BaseCommand):
            def __init__(self) -> None:
                metadata = CommandMetadata(
                    name="test:another",
                    category=CommandCategory.SYSTEM,
                    description="Another mock command",
                    help_text="/test:another",
                )
                super().__init__(metadata)

            async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
                return {"success": True}

        cmd2 = AnotherMockCommand()

        registry.register(cmd1, aliases=["duplicate"])

        with pytest.raises(ValueError, match="Alias.*already registered"):
            registry.register(cmd2, aliases=["duplicate"])

    def test_get_command_help_nonexistent(self) -> None:
        """Test get_command_help returns None for nonexistent command"""
        registry = CommandRegistry()

        help_text = registry.get_command_help("nonexistent")

        assert help_text is None

    @pytest.mark.asyncio
    async def test_execute_command_exception_handling(self) -> None:
        """Test execute handles command execution exceptions"""

        class FailingCommand(BaseCommand):
            def __init__(self) -> None:
                metadata = CommandMetadata(
                    name="test:failing",
                    category=CommandCategory.SYSTEM,
                    description="Failing command",
                    help_text="/test:failing",
                )
                super().__init__(metadata)

            async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
                raise RuntimeError("Intentional failure")

        registry = CommandRegistry()
        cmd = FailingCommand()
        registry.register(cmd)

        result = await registry.execute("test:failing", {})

        assert result["success"] is False
        assert "error" in result
        assert "Intentional failure" in result["error"]
        assert result["command"] == "test:failing"

    def test_list_categories_empty_registry(self) -> None:
        """Test list_categories with empty registry"""
        registry = CommandRegistry()

        categories = registry.list_categories()

        assert len(categories) == 0

    def test_repr(self) -> None:
        """Test string representation of registry"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd)

        repr_str = repr(registry)

        assert "CommandRegistry" in repr_str
        assert "commands=1" in repr_str
        assert "categories=" in repr_str

    def test_discover_commands_skips_special_modules(self) -> None:
        """Test discover_commands skips base and registry modules"""
        from pathlib import Path

        from src.core.commands import registry as reg_module

        registry = CommandRegistry()
        package_path = Path(reg_module.__file__).parent

        # This should discover actual commands but skip base.py and registry.py
        count = registry.discover_commands(package_path)

        # Should discover legal_help and legal_research (2 commands)
        assert count >= 2
        assert "legal:help" in registry
        assert "legal:research" in registry

    def test_discover_commands_handles_import_errors(self) -> None:
        """Test discover_commands handles module import failures gracefully"""
        import tempfile
        from pathlib import Path

        # Create temporary directory with invalid Python file
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a Python file with syntax error
            bad_file = tmppath / "bad_module.py"
            bad_file.write_text("This is not valid Python syntax !")

            # Create an __init__.py to make it a package
            (tmppath / "__init__.py").write_text("")

            registry = CommandRegistry()

            # Should handle import error gracefully and continue
            count = registry.discover_commands(tmppath)

            # Should return 0 (no valid commands discovered)
            assert count == 0

    def test_get_command_nonexistent_returns_none(self) -> None:
        """Test get_command returns None for nonexistent command"""
        registry = CommandRegistry()

        cmd = registry.get_command("nonexistent")

        assert cmd is None

    def test_contains_with_alias(self) -> None:
        """Test __contains__ works with both names and aliases"""
        registry = CommandRegistry()
        cmd = MockCommand()
        registry.register(cmd, aliases=["alias1", "alias2"])

        assert "test:mock" in registry
        assert "alias1" in registry
        assert "alias2" in registry
        assert "nonexistent" not in registry
