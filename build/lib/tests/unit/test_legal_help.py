"""
Unit tests for Legal Help Command

Tests the LegalHelpCommand functionality including:
- Help command execution
- Categories formatting
- Command listing
- Argument descriptions
- Verbose mode
"""

import pytest

from src.core.commands.legal_help import LegalHelpCommand


class TestLegalHelpCommand:
    """Test Legal Help Command functionality"""

    def test_command_initialization(self) -> None:
        """Test help command initializes with correct metadata"""
        cmd = LegalHelpCommand()

        assert cmd.metadata.name == "legal:help"
        assert cmd.metadata.category.value == "system"
        assert "commands" in cmd.metadata.description.lower()
        assert len(cmd.arguments) == 3  # category, command, verbose

    def test_arguments_configuration(self) -> None:
        """Test help command has correct arguments"""
        cmd = LegalHelpCommand()

        arg_names = [arg.name for arg in cmd.arguments]
        assert "category" in arg_names
        assert "command" in arg_names
        assert "verbose" in arg_names

        # Verify all arguments are optional
        for arg in cmd.arguments:
            assert arg.required is False

    @pytest.mark.asyncio
    async def test_help_command_execution_success(self) -> None:
        """Test help command executes successfully"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({})

        assert result["success"] is True
        assert "help_text" in result
        assert len(result["help_text"]) > 0

    @pytest.mark.asyncio
    async def test_general_help_shows_categories(self) -> None:
        """Test general help displays command categories"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({})

        assert "categories" in result
        assert "RESEARCH" in result["categories"]
        assert "SYSTEM" in result["categories"]
        assert "BetterCallClaude" in result["help_text"]

    @pytest.mark.asyncio
    async def test_general_help_lists_commands(self) -> None:
        """Test general help lists available commands"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({})

        help_text = result["help_text"]
        assert "legal:research" in help_text
        assert "legal:help" in help_text
        assert "RESEARCH:" in help_text
        assert "SYSTEM:" in help_text

    @pytest.mark.asyncio
    async def test_category_filter(self) -> None:
        """Test filtering help by category"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({"category": "research"})

        assert result["success"] is True
        assert "Filtered by category" in result["help_text"]
        assert "legal:research" in result["help_text"]

    @pytest.mark.asyncio
    async def test_command_specific_help(self) -> None:
        """Test getting help for specific command"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({"command": "legal:research"})

        assert result["success"] is True
        assert result["command"] == "legal:research"
        assert "legal:research" in result["help_text"]
        assert "Command:" in result["help_text"]

    @pytest.mark.asyncio
    async def test_verbose_mode_metadata(self) -> None:
        """Test verbose flag is captured in metadata"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({"verbose": True})

        assert result["metadata"]["verbose"] is True

    @pytest.mark.asyncio
    async def test_help_text_formatting(self) -> None:
        """Test help text is properly formatted"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({})

        help_text = result["help_text"]

        # Check for key sections
        assert "Available Commands:" in help_text
        assert "Usage:" in help_text
        assert "RESEARCH:" in help_text
        assert "SYSTEM:" in help_text

        # Check formatting consistency
        lines = help_text.split("\n")
        assert len(lines) > 5  # Multi-line output

    @pytest.mark.asyncio
    async def test_help_includes_usage_examples(self) -> None:
        """Test help includes usage examples"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({})

        help_text = result["help_text"]
        assert "--command=" in help_text
        assert "--category=" in help_text
        assert "--verbose" in help_text

    @pytest.mark.asyncio
    async def test_command_descriptions_present(self) -> None:
        """Test command descriptions are included"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({})

        help_text = result["help_text"]
        assert "Search Swiss legal sources" in help_text
        assert "Display this help message" in help_text

    @pytest.mark.asyncio
    async def test_category_case_insensitive(self) -> None:
        """Test category filter is case insensitive"""
        cmd = LegalHelpCommand()

        result_lower = await cmd.execute({"category": "research"})
        result_upper = await cmd.execute({"category": "RESEARCH"})

        assert result_lower["success"] is True
        assert result_upper["success"] is True
        assert "legal:research" in result_lower["help_text"]
        assert "legal:research" in result_upper["help_text"]

    @pytest.mark.asyncio
    async def test_empty_args_shows_general_help(self) -> None:
        """Test empty arguments shows general help"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({})

        assert result["success"] is True
        assert "categories" in result
        assert len(result["categories"]) > 0

    @pytest.mark.asyncio
    async def test_metadata_includes_filters(self) -> None:
        """Test metadata captures filter parameters"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({"category": "research", "verbose": True})

        metadata = result["metadata"]
        assert metadata["category_filter"] == "research"
        assert metadata["verbose"] is True

    def test_command_metadata_structure(self) -> None:
        """Test command metadata has required fields"""
        cmd = LegalHelpCommand()

        assert hasattr(cmd.metadata, "name")
        assert hasattr(cmd.metadata, "category")
        assert hasattr(cmd.metadata, "description")
        assert hasattr(cmd.metadata, "help_text")
        assert cmd.metadata.auto_personas == []
        assert cmd.metadata.mcp_servers == []
        assert cmd.metadata.requires_auth is False

    @pytest.mark.asyncio
    async def test_help_for_unknown_command(self) -> None:
        """Test help for unknown command returns gracefully"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({"command": "unknown:command"})

        assert result["success"] is True
        assert "unknown:command" in result["help_text"]

    @pytest.mark.asyncio
    async def test_specific_command_help_structure(self) -> None:
        """Test specific command help has expected structure"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({"command": "legal:research"})

        assert "command" in result
        assert "help_text" in result
        assert "metadata" in result
        assert result["command"] == "legal:research"

    @pytest.mark.asyncio
    async def test_help_text_no_trailing_whitespace(self) -> None:
        """Test help text is stripped of trailing whitespace"""
        cmd = LegalHelpCommand()
        result = await cmd.execute({})

        help_text = result["help_text"]
        assert help_text == help_text.strip()

    def test_argument_help_text_present(self) -> None:
        """Test all arguments have help text"""
        cmd = LegalHelpCommand()

        for arg in cmd.arguments:
            assert arg.help_text is not None
            assert len(arg.help_text) > 0

    def test_category_argument_lists_options(self) -> None:
        """Test category argument lists valid options"""
        cmd = LegalHelpCommand()

        category_arg = next(arg for arg in cmd.arguments if arg.name == "category")
        assert "research" in category_arg.help_text
        assert "system" in category_arg.help_text
