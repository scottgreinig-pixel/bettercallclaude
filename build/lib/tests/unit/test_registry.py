"""
Unit tests for Agent Registry

Tests the AgentRegistry, AgentDescriptor, and related classes from src/agents/registry.py
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from src.agents.registry import (
    AgentCapability,
    AgentCategory,
    AgentDescriptor,
    AgentInputSchema,
    AgentOutputSchema,
    AgentRegistry,
    get_registry,
    refresh_registry,
)

# =============================================================================
# AgentCategory Tests
# =============================================================================


class TestAgentCategory:
    """Test AgentCategory enum."""

    def test_enum_values(self) -> None:
        """Test category enum has correct values."""
        assert AgentCategory.RESEARCH.value == "research"
        assert AgentCategory.STRATEGY.value == "strategy"
        assert AgentCategory.DRAFTING.value == "drafting"
        assert AgentCategory.ANALYSIS.value == "analysis"
        assert AgentCategory.COMPLIANCE.value == "compliance"
        assert AgentCategory.SPECIALIZED.value == "specialized"
        assert AgentCategory.UTILITY.value == "utility"

    def test_enum_from_string(self) -> None:
        """Test creating enum from string value."""
        assert AgentCategory("research") == AgentCategory.RESEARCH
        assert AgentCategory("strategy") == AgentCategory.STRATEGY
        assert AgentCategory("drafting") == AgentCategory.DRAFTING

    def test_all_categories_exist(self) -> None:
        """Test that all expected categories exist."""
        expected = {
            "research",
            "strategy",
            "drafting",
            "analysis",
            "compliance",
            "specialized",
            "utility",
        }
        actual = {c.value for c in AgentCategory}
        assert actual == expected


# =============================================================================
# AgentCapability Tests
# =============================================================================


class TestAgentCapability:
    """Test AgentCapability data class."""

    def test_create_capability_minimal(self) -> None:
        """Test creating capability with minimal fields."""
        cap = AgentCapability(name="search", description="Search capability")

        assert cap.name == "search"
        assert cap.description == "Search capability"
        assert cap.input_types == []
        assert cap.output_types == []

    def test_create_capability_full(self) -> None:
        """Test creating capability with all fields."""
        cap = AgentCapability(
            name="legal_research",
            description="Deep legal research",
            input_types=["query", "jurisdiction"],
            output_types=["ResearchMemo"],
        )

        assert cap.name == "legal_research"
        assert cap.description == "Deep legal research"
        assert cap.input_types == ["query", "jurisdiction"]
        assert cap.output_types == ["ResearchMemo"]


# =============================================================================
# AgentInputSchema Tests
# =============================================================================


class TestAgentInputSchema:
    """Test AgentInputSchema data class."""

    def test_create_schema_defaults(self) -> None:
        """Test creating schema with defaults."""
        schema = AgentInputSchema()

        assert schema.required == {}
        assert schema.optional == {}
        assert schema.defaults == {}

    def test_create_schema_full(self) -> None:
        """Test creating schema with all fields."""
        schema = AgentInputSchema(
            required={"task": "str", "jurisdiction": "str"},
            optional={"language": "str"},
            defaults={"language": "DE"},
        )

        assert schema.required == {"task": "str", "jurisdiction": "str"}
        assert schema.optional == {"language": "str"}
        assert schema.defaults == {"language": "DE"}


# =============================================================================
# AgentOutputSchema Tests
# =============================================================================


class TestAgentOutputSchema:
    """Test AgentOutputSchema data class."""

    def test_create_schema_defaults(self) -> None:
        """Test creating output schema with defaults."""
        schema = AgentOutputSchema()

        assert schema.primary_type == "AgentResult"
        assert schema.deliverable_type == "Any"
        assert schema.includes_checkpoints is True
        assert schema.includes_audit_log is True

    def test_create_schema_custom(self) -> None:
        """Test creating output schema with custom values."""
        schema = AgentOutputSchema(
            primary_type="ResearchResult",
            deliverable_type="ResearchMemo",
            includes_checkpoints=False,
            includes_audit_log=True,
        )

        assert schema.primary_type == "ResearchResult"
        assert schema.deliverable_type == "ResearchMemo"
        assert schema.includes_checkpoints is False


# =============================================================================
# AgentDescriptor Tests
# =============================================================================


class TestAgentDescriptor:
    """Test AgentDescriptor data class."""

    def test_create_python_agent_descriptor(self) -> None:
        """Test creating a Python agent descriptor."""
        descriptor = AgentDescriptor(
            agent_id="researcher",
            name="ResearcherAgent",
            version="1.0.0",
            description="Legal research agent",
            agent_type="python",
            category=AgentCategory.RESEARCH,
            module_path="src.agents.researcher",
            class_name="ResearcherAgent",
        )

        assert descriptor.agent_id == "researcher"
        assert descriptor.name == "ResearcherAgent"
        assert descriptor.version == "1.0.0"
        assert descriptor.agent_type == "python"
        assert descriptor.category == AgentCategory.RESEARCH
        assert descriptor.module_path == "src.agents.researcher"
        assert descriptor.class_name == "ResearcherAgent"
        assert descriptor.command_path is None
        assert descriptor.supports_parallel is True
        assert descriptor.priority == 100

    def test_create_command_agent_descriptor(self) -> None:
        """Test creating a command agent descriptor."""
        descriptor = AgentDescriptor(
            agent_id="risk",
            name="Risk Assessment Agent",
            version="1.0.0",
            description="Risk assessment for legal cases",
            agent_type="command",
            category=AgentCategory.ANALYSIS,
            command_path="/path/to/agent:risk.md",
            command_name="/agent:risk",
        )

        assert descriptor.agent_id == "risk"
        assert descriptor.agent_type == "command"
        assert descriptor.category == AgentCategory.ANALYSIS
        assert descriptor.command_path == "/path/to/agent:risk.md"
        assert descriptor.command_name == "/agent:risk"
        assert descriptor.module_path is None

    def test_descriptor_to_dict(self) -> None:
        """Test serializing descriptor to dictionary."""
        cap = AgentCapability(name="search", description="Search capability")
        descriptor = AgentDescriptor(
            agent_id="test",
            name="TestAgent",
            version="2.0.0",
            description="Test agent",
            agent_type="python",
            category=AgentCategory.UTILITY,
            capabilities=[cap],
            tags=["test", "utility"],
            priority=50,
        )

        data = descriptor.to_dict()

        assert data["agent_id"] == "test"
        assert data["name"] == "TestAgent"
        assert data["version"] == "2.0.0"
        assert data["agent_type"] == "python"
        assert data["category"] == "utility"
        assert len(data["capabilities"]) == 1
        assert data["capabilities"][0]["name"] == "search"
        assert data["tags"] == ["test", "utility"]
        assert data["priority"] == 50

    def test_descriptor_defaults(self) -> None:
        """Test descriptor has correct defaults."""
        descriptor = AgentDescriptor(
            agent_id="minimal",
            name="Minimal",
            version="1.0.0",
            description="Minimal agent",
            agent_type="python",
            category=AgentCategory.UTILITY,
        )

        assert descriptor.capabilities == []
        assert descriptor.tags == []
        assert descriptor.supports_parallel is True
        assert descriptor.supports_checkpoints is True
        assert descriptor.supports_sub_agents is False
        assert descriptor.default_autonomy_mode == "balanced"
        assert descriptor.priority == 100

    def test_get_agent_class_for_command_agent(self) -> None:
        """Test that get_agent_class returns None for command agents."""
        descriptor = AgentDescriptor(
            agent_id="command_agent",
            name="Command Agent",
            version="1.0.0",
            description="A command agent",
            agent_type="command",
            category=AgentCategory.UTILITY,
        )

        assert descriptor.get_agent_class() is None

    def test_get_agent_class_missing_module(self) -> None:
        """Test get_agent_class with missing module path."""
        descriptor = AgentDescriptor(
            agent_id="no_module",
            name="No Module",
            version="1.0.0",
            description="Agent without module",
            agent_type="python",
            category=AgentCategory.UTILITY,
        )

        assert descriptor.get_agent_class() is None


# =============================================================================
# AgentRegistry Tests - Core Functionality
# =============================================================================


class TestAgentRegistryCore:
    """Test AgentRegistry core functionality."""

    def test_registry_initialization(self) -> None:
        """Test registry initializes with discovered agents."""
        registry = AgentRegistry()

        # Should have discovered at least the known Python agents
        assert len(registry) >= 3
        assert "researcher" in registry
        assert "strategist" in registry
        assert "drafter" in registry

    def test_registry_repr(self) -> None:
        """Test registry string representation."""
        registry = AgentRegistry()
        repr_str = repr(registry)

        assert "AgentRegistry" in repr_str
        assert "python=" in repr_str
        assert "command=" in repr_str
        assert "total=" in repr_str

    def test_registry_len(self) -> None:
        """Test registry length."""
        registry = AgentRegistry()
        assert len(registry) > 0

    def test_registry_contains(self) -> None:
        """Test registry contains operator."""
        registry = AgentRegistry()
        assert "researcher" in registry
        assert "nonexistent_agent" not in registry

    def test_registry_iter(self) -> None:
        """Test registry iteration."""
        registry = AgentRegistry()
        agents = list(registry)
        assert len(agents) > 0
        assert all(isinstance(a, AgentDescriptor) for a in agents)


# =============================================================================
# AgentRegistry Tests - Discovery
# =============================================================================


class TestAgentRegistryDiscovery:
    """Test agent discovery functionality."""

    def test_discover_python_agents(self) -> None:
        """Test Python agent discovery."""
        registry = AgentRegistry()
        python_agents = registry.get_python_agents()

        # Should find the known Python agents
        agent_ids = {a.agent_id for a in python_agents}
        assert "researcher" in agent_ids
        assert "strategist" in agent_ids
        assert "drafter" in agent_ids

        # All should be Python type
        for agent in python_agents:
            assert agent.agent_type == "python"
            assert agent.module_path is not None
            assert agent.class_name is not None

    def test_discover_command_agents(self) -> None:
        """Test command agent discovery."""
        registry = AgentRegistry()
        command_agents = registry.get_command_agents()

        # Should find command agents if they exist
        for agent in command_agents:
            assert agent.agent_type == "command"
            assert agent.command_path is not None
            assert agent.command_name is not None
            assert agent.command_name.startswith("/agent:")

    def test_refresh_discovery(self) -> None:
        """Test that discover_agents can be called multiple times."""
        registry = AgentRegistry()
        initial_count = len(registry)

        # Re-discover
        new_count = registry.discover_agents()

        assert new_count == initial_count

    def test_custom_commands_dir(self) -> None:
        """Test registry with custom commands directory."""
        with TemporaryDirectory() as tmpdir:
            # Create a mock command file
            cmd_file = Path(tmpdir) / "agent:test.md"
            cmd_file.write_text(
                """# /agent:test - Test Agent

**Version**: 1.0.0
**Domain**: Testing

A test agent for unit testing.

## What This Agent Does
- **testing**: Runs tests
"""
            )

            registry = AgentRegistry(commands_dir=tmpdir)

            # Should find the test agent
            assert "test" in registry
            test_agent = registry.get_agent("test")
            assert test_agent is not None
            assert test_agent.agent_type == "command"
            assert test_agent.version == "1.0.0"

    def test_nonexistent_commands_dir(self) -> None:
        """Test registry with nonexistent commands directory."""
        registry = AgentRegistry(commands_dir="/nonexistent/path", auto_discover=True)

        # Should still have Python agents
        assert "researcher" in registry


# =============================================================================
# AgentRegistry Tests - Retrieval
# =============================================================================


class TestAgentRegistryRetrieval:
    """Test agent retrieval functionality."""

    def test_get_agent(self) -> None:
        """Test getting agent by ID."""
        registry = AgentRegistry()

        researcher = registry.get_agent("researcher")
        assert researcher is not None
        assert researcher.agent_id == "researcher"
        assert researcher.category == AgentCategory.RESEARCH

    def test_get_agent_not_found(self) -> None:
        """Test getting nonexistent agent."""
        registry = AgentRegistry()

        agent = registry.get_agent("nonexistent")
        assert agent is None

    def test_list_agents(self) -> None:
        """Test listing all agents."""
        registry = AgentRegistry()
        agents = registry.list_agents()

        assert len(agents) > 0
        # Should be sorted by priority
        priorities = [a.priority for a in agents]
        assert priorities == sorted(priorities)

    def test_list_agent_ids(self) -> None:
        """Test listing agent IDs."""
        registry = AgentRegistry()
        ids = registry.list_agent_ids()

        assert isinstance(ids, list)
        assert "researcher" in ids
        assert ids == sorted(ids)

    def test_is_registered(self) -> None:
        """Test checking if agent is registered."""
        registry = AgentRegistry()

        assert registry.is_registered("researcher") is True
        assert registry.is_registered("nonexistent") is False


# =============================================================================
# AgentRegistry Tests - Filtering
# =============================================================================


class TestAgentRegistryFiltering:
    """Test agent filtering functionality."""

    def test_get_agents_by_category(self) -> None:
        """Test filtering by category."""
        registry = AgentRegistry()

        research_agents = registry.get_agents_by_category(AgentCategory.RESEARCH)
        assert len(research_agents) >= 1
        assert all(a.category == AgentCategory.RESEARCH for a in research_agents)

        strategy_agents = registry.get_agents_by_category(AgentCategory.STRATEGY)
        assert len(strategy_agents) >= 1
        assert all(a.category == AgentCategory.STRATEGY for a in strategy_agents)

    def test_get_agents_by_capability(self) -> None:
        """Test filtering by capability."""
        registry = AgentRegistry()

        # Researcher should have legal_research capability
        research_capable = registry.get_agents_by_capability("legal_research")
        agent_ids = [a.agent_id for a in research_capable]
        assert "researcher" in agent_ids

    def test_get_agents_by_tag(self) -> None:
        """Test filtering by tag."""
        registry = AgentRegistry()

        # Researcher should have "research" tag
        research_tagged = registry.get_agents_by_tag("research")
        agent_ids = [a.agent_id for a in research_tagged]
        assert "researcher" in agent_ids

    def test_get_agents_by_type(self) -> None:
        """Test filtering by implementation type."""
        registry = AgentRegistry()

        python_agents = registry.get_agents_by_type("python")
        assert len(python_agents) >= 3  # researcher, strategist, drafter
        assert all(a.agent_type == "python" for a in python_agents)

        command_agents = registry.get_agents_by_type("command")
        assert all(a.agent_type == "command" for a in command_agents)


# =============================================================================
# AgentRegistry Tests - Search
# =============================================================================


class TestAgentRegistrySearch:
    """Test agent search functionality."""

    def test_search_by_exact_id(self) -> None:
        """Test searching by exact agent ID."""
        registry = AgentRegistry()

        results = registry.search_agents("researcher")
        assert len(results) > 0
        assert results[0].agent_id == "researcher"

    def test_search_by_partial_id(self) -> None:
        """Test searching by partial agent ID."""
        registry = AgentRegistry()

        results = registry.search_agents("research")
        assert len(results) > 0
        # Researcher should be in results
        assert any(a.agent_id == "researcher" for a in results)

    def test_search_by_description(self) -> None:
        """Test searching by description content."""
        registry = AgentRegistry()

        results = registry.search_agents("legal")
        assert len(results) > 0

    def test_search_no_results(self) -> None:
        """Test search with no matching results."""
        registry = AgentRegistry()

        results = registry.search_agents("xyz123nonexistent")
        assert len(results) == 0

    def test_search_case_insensitive(self) -> None:
        """Test that search is case-insensitive."""
        registry = AgentRegistry()

        lower_results = registry.search_agents("researcher")
        upper_results = registry.search_agents("RESEARCHER")
        mixed_results = registry.search_agents("ReSearcher")

        assert len(lower_results) == len(upper_results) == len(mixed_results)


# =============================================================================
# AgentRegistry Tests - Command File Parsing
# =============================================================================


class TestCommandFileParsing:
    """Test command file parsing functionality."""

    def test_parse_command_file_with_all_fields(self) -> None:
        """Test parsing a well-formed command file."""
        with TemporaryDirectory() as tmpdir:
            cmd_file = Path(tmpdir) / "agent:complete.md"
            cmd_file.write_text(
                """# /agent:complete - Complete Test Agent

**Version**: 2.5.0
**Domain**: Complete Testing
**Agent**: A complete agent with all metadata

This is a comprehensive test agent.

## What This Agent Does
- **analysis**: Analyzes data thoroughly
- **reporting**: Generates detailed reports
"""
            )

            registry = AgentRegistry(commands_dir=tmpdir)
            agent = registry.get_agent("complete")

            assert agent is not None
            assert agent.agent_id == "complete"
            assert agent.name == "Complete Test Agent"
            assert agent.version == "2.5.0"
            assert agent.description == "A complete agent with all metadata"
            assert len(agent.capabilities) >= 1

    def test_parse_command_file_minimal(self) -> None:
        """Test parsing a minimal command file."""
        with TemporaryDirectory() as tmpdir:
            cmd_file = Path(tmpdir) / "agent:minimal.md"
            cmd_file.write_text(
                """# Minimal Agent

A minimal agent without standard formatting.
"""
            )

            registry = AgentRegistry(commands_dir=tmpdir)
            agent = registry.get_agent("minimal")

            assert agent is not None
            assert agent.agent_id == "minimal"
            assert agent.version == "1.0.0"  # Default version

    def test_skip_orchestrator_file(self) -> None:
        """Test that orchestrator file is skipped."""
        with TemporaryDirectory() as tmpdir:
            # Create orchestrator file
            orch_file = Path(tmpdir) / "agent:orchestrator.md"
            orch_file.write_text("# Orchestrator - should be skipped")

            # Create regular agent file
            agent_file = Path(tmpdir) / "agent:regular.md"
            agent_file.write_text("# Regular Agent")

            registry = AgentRegistry(commands_dir=tmpdir)

            # Orchestrator should not be registered
            assert "orchestrator" not in registry
            assert "regular" in registry


# =============================================================================
# Global Registry Tests
# =============================================================================


class TestGlobalRegistry:
    """Test global registry functions."""

    def test_get_registry_singleton(self) -> None:
        """Test that get_registry returns singleton."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_refresh_registry(self) -> None:
        """Test that refresh_registry creates new instance."""
        _old_registry = get_registry()
        new_registry = refresh_registry()

        # After refresh, get_registry should return the new instance
        current = get_registry()
        assert current is new_registry


# =============================================================================
# Integration Tests
# =============================================================================


class TestRegistryIntegration:
    """Integration tests for registry with real project structure."""

    def test_python_agent_metadata_accuracy(self) -> None:
        """Test that Python agent metadata is accurate."""
        registry = AgentRegistry()

        researcher = registry.get_agent("researcher")
        assert researcher is not None
        assert researcher.category == AgentCategory.RESEARCH
        assert "research" in researcher.tags
        assert len(researcher.capabilities) > 0

        strategist = registry.get_agent("strategist")
        assert strategist is not None
        assert strategist.category == AgentCategory.STRATEGY
        assert "strategy" in strategist.tags

        drafter = registry.get_agent("drafter")
        assert drafter is not None
        assert drafter.category == AgentCategory.DRAFTING
        assert "drafting" in drafter.tags

    def test_python_agents_higher_priority(self) -> None:
        """Test that Python agents have higher priority than command agents."""
        registry = AgentRegistry()

        python_agents = registry.get_python_agents()
        command_agents = registry.get_command_agents()

        if python_agents and command_agents:
            max_python_priority = max(a.priority for a in python_agents)
            min_command_priority = min(a.priority for a in command_agents)

            # Python agents should have lower priority values (higher priority)
            assert max_python_priority < min_command_priority

    def test_all_agents_have_required_fields(self) -> None:
        """Test that all discovered agents have required fields."""
        registry = AgentRegistry()

        for agent in registry:
            assert agent.agent_id is not None
            assert len(agent.agent_id) > 0
            assert agent.name is not None
            assert agent.version is not None
            assert agent.description is not None
            assert agent.agent_type in ("python", "command")
            assert agent.category is not None
            assert isinstance(agent.category, AgentCategory)

    def test_category_coverage(self) -> None:
        """Test that agents cover multiple categories."""
        registry = AgentRegistry()

        categories_found = {a.category for a in registry}

        # Should have at least research, strategy, and drafting
        assert AgentCategory.RESEARCH in categories_found
        assert AgentCategory.STRATEGY in categories_found
        assert AgentCategory.DRAFTING in categories_found
