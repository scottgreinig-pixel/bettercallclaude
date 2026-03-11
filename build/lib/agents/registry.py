"""
BetterCallClaude Agent Registry

Unified agent discovery and management system that supports both Python-based agents
and command-based agents (slash commands). This enables the orchestrator to work with
all available agents dynamically.

Architecture:
- AgentDescriptor: Unified metadata for any agent type
- AgentRegistry: Auto-discovers and manages all available agents
- Supports Python agents (class-based) and Command agents (markdown-based)
"""

import importlib
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)


# =============================================================================
# Agent Type Definitions
# =============================================================================


class AgentCategory(Enum):
    """Categories of agents for routing and filtering."""

    RESEARCH = "research"
    STRATEGY = "strategy"
    DRAFTING = "drafting"
    ANALYSIS = "analysis"
    COMPLIANCE = "compliance"
    SPECIALIZED = "specialized"
    UTILITY = "utility"


@dataclass
class AgentCapability:
    """Describes a specific capability of an agent."""

    name: str
    description: str
    input_types: list[str] = field(default_factory=list)
    output_types: list[str] = field(default_factory=list)


@dataclass
class AgentInputSchema:
    """Schema for agent inputs."""

    required: dict[str, str] = field(default_factory=dict)  # name: type
    optional: dict[str, str] = field(default_factory=dict)  # name: type
    defaults: dict[str, Any] = field(default_factory=dict)  # name: default_value


@dataclass
class AgentOutputSchema:
    """Schema for agent outputs."""

    primary_type: str = "AgentResult"
    deliverable_type: str = "Any"
    includes_checkpoints: bool = True
    includes_audit_log: bool = True


@dataclass
class AgentDescriptor:
    """
    Unified agent metadata regardless of implementation type.

    This descriptor allows the orchestrator to work with any agent
    without knowing the underlying implementation details.
    """

    # Identity
    agent_id: str
    name: str
    version: str
    description: str

    # Implementation type
    agent_type: Literal["python", "command"]

    # Classification
    category: AgentCategory
    capabilities: list[AgentCapability] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Schemas
    input_schema: AgentInputSchema = field(default_factory=AgentInputSchema)
    output_schema: AgentOutputSchema = field(default_factory=AgentOutputSchema)

    # For Python agents
    module_path: str | None = None
    class_name: str | None = None
    _agent_class: type | None = field(default=None, repr=False)

    # For command agents
    command_path: str | None = None
    command_name: str | None = None

    # Integration settings
    supports_parallel: bool = True
    supports_checkpoints: bool = True
    supports_sub_agents: bool = False
    default_autonomy_mode: str = "balanced"

    # Priority for routing (lower = higher priority)
    priority: int = 100

    def get_agent_class(self) -> type | None:
        """
        Lazy-load the agent class for Python agents.

        Returns:
            The agent class if this is a Python agent, None otherwise.
        """
        if self.agent_type != "python":
            return None

        if self._agent_class is not None:
            return self._agent_class

        if self.module_path and self.class_name:
            try:
                module = importlib.import_module(self.module_path)
                self._agent_class = getattr(module, self.class_name)
                return self._agent_class
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to load agent class {self.class_name}: {e}")
                return None

        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize descriptor to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "agent_type": self.agent_type,
            "category": self.category.value,
            "capabilities": [
                {"name": c.name, "description": c.description} for c in self.capabilities
            ],
            "tags": self.tags,
            "supports_parallel": self.supports_parallel,
            "supports_checkpoints": self.supports_checkpoints,
            "priority": self.priority,
        }


# =============================================================================
# Agent Registry
# =============================================================================


class AgentRegistry:
    """
    Auto-discovers and manages all available agents.

    Scans for:
    1. Python agent classes in src/agents/
    2. Command agent definitions in .claude/commands/agent:*.md

    Provides unified access to all agents regardless of implementation type.
    """

    # Known Python agents with their metadata
    PYTHON_AGENTS = {
        "researcher": {
            "module": "src.agents.researcher",
            "class": "ResearcherAgent",
            "category": AgentCategory.RESEARCH,
            "description": "Legal research with multi-source search and citation verification",
            "capabilities": [
                AgentCapability(
                    name="legal_research",
                    description="Deep legal research across Swiss law sources",
                    input_types=["query", "jurisdiction", "language"],
                    output_types=["ResearchMemo"],
                ),
                AgentCapability(
                    name="citation_verification",
                    description="Verify and format legal citations",
                    input_types=["citations"],
                    output_types=["VerificationReport"],
                ),
            ],
            "tags": ["research", "bge", "precedents", "citations"],
        },
        "strategist": {
            "module": "src.agents.strategist",
            "class": "StrategistAgent",
            "category": AgentCategory.STRATEGY,
            "description": "Litigation strategy development and risk assessment",
            "capabilities": [
                AgentCapability(
                    name="strategy_development",
                    description="Develop comprehensive litigation strategies",
                    input_types=["case_facts", "jurisdiction"],
                    output_types=["StrategyRecommendation"],
                ),
                AgentCapability(
                    name="risk_assessment",
                    description="Assess case risks and success probabilities",
                    input_types=["case_facts", "research_results"],
                    output_types=["RiskAssessment"],
                ),
            ],
            "tags": ["strategy", "litigation", "risk", "planning"],
        },
        "drafter": {
            "module": "src.agents.drafter",
            "class": "DrafterAgent",
            "category": AgentCategory.DRAFTING,
            "description": "Legal document drafting with template support",
            "capabilities": [
                AgentCapability(
                    name="document_drafting",
                    description="Draft legal documents from templates",
                    input_types=["document_type", "case_facts", "strategy"],
                    output_types=["LegalDocument"],
                ),
            ],
            "tags": ["drafting", "documents", "klageschrift", "memorandum"],
        },
    }

    # Command file parsing patterns
    COMMAND_PATTERNS = {
        "title": r"^#\s+/agent:(\w+)\s*[-–]\s*(.+)$",
        "version": r"\*\*Version\*\*:\s*(\d+\.\d+\.\d+)",
        "domain": r"\*\*Domain\*\*:\s*(.+)",
        "description": r"\*\*Agent\*\*:\s*(.+)",
    }

    def __init__(
        self,
        commands_dir: str | Path | None = None,
        auto_discover: bool = True,
    ):
        """
        Initialize the agent registry.

        Args:
            commands_dir: Path to .claude/commands directory
            auto_discover: Whether to auto-discover agents on init
        """
        self._agents: dict[str, AgentDescriptor] = {}
        self._by_category: dict[AgentCategory, list[str]] = {}
        self._by_capability: dict[str, list[str]] = {}

        # Determine commands directory
        if commands_dir:
            self.commands_dir = Path(commands_dir)
        else:
            # Default to project's .claude/commands
            self.commands_dir = Path(__file__).parent.parent.parent / ".claude" / "commands"

        if auto_discover:
            self.discover_agents()

    def discover_agents(self) -> int:
        """
        Discover all available agents.

        Returns:
            Number of agents discovered.
        """
        self._agents.clear()
        self._by_category.clear()
        self._by_capability.clear()

        # Discover Python agents
        python_count = self._discover_python_agents()
        logger.info(f"Discovered {python_count} Python agents")

        # Discover command agents
        command_count = self._discover_command_agents()
        logger.info(f"Discovered {command_count} command agents")

        # Build indexes
        self._build_indexes()

        total = len(self._agents)
        logger.info(f"Total agents registered: {total}")
        return total

    def _discover_python_agents(self) -> int:
        """
        Discover and register Python-based agents.

        Returns:
            Number of Python agents discovered.
        """
        count = 0

        for agent_id, config in self.PYTHON_AGENTS.items():
            try:
                name: str = str(config.get("class", agent_id.title()))
                module_path: str = str(config["module"])
                class_name: str = str(config["class"])
                description: str = str(config["description"])
                category: AgentCategory = config["category"]  # type: ignore[assignment]
                capabilities: list[AgentCapability] = config.get("capabilities", [])  # type: ignore[assignment]
                tags: list[str] = config.get("tags", [])  # type: ignore[assignment]

                descriptor = AgentDescriptor(
                    agent_id=agent_id,
                    name=name,
                    version=self._get_python_agent_version(module_path, class_name),
                    description=description,
                    agent_type="python",
                    category=category,
                    capabilities=capabilities,
                    tags=tags,
                    module_path=module_path,
                    class_name=class_name,
                    supports_parallel=True,
                    supports_checkpoints=True,
                    supports_sub_agents=True,
                    priority=10,  # Python agents have higher priority
                )

                self._agents[agent_id] = descriptor
                count += 1
                logger.debug(f"Registered Python agent: {agent_id}")

            except Exception as e:
                logger.warning(f"Failed to register Python agent {agent_id}: {e}")

        return count

    def _get_python_agent_version(self, module_path: str, class_name: str) -> str:
        """Get version from Python agent class."""
        try:
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            # Try to get version from class attribute or instance
            if hasattr(agent_class, "VERSION"):
                return str(agent_class.VERSION)
            # Create temporary instance to get version property
            # This is a bit hacky but works for our agents
            return "1.0.0"
        except Exception:
            return "1.0.0"

    def _discover_command_agents(self) -> int:
        """
        Discover and register command-based agents from .md files.

        Returns:
            Number of command agents discovered.
        """
        count = 0

        if not self.commands_dir.exists():
            logger.warning(f"Commands directory not found: {self.commands_dir}")
            return 0

        # Find all agent:*.md files
        for cmd_file in self.commands_dir.glob("agent:*.md"):
            try:
                # Skip orchestrator (it's the coordinator, not an agent)
                if "orchestrator" in cmd_file.name:
                    continue

                descriptor = self._parse_command_file(cmd_file)
                if descriptor:
                    # Skip if already registered as Python agent
                    if descriptor.agent_id not in self._agents:
                        self._agents[descriptor.agent_id] = descriptor
                        count += 1
                        logger.debug(f"Registered command agent: {descriptor.agent_id}")

            except Exception as e:
                logger.warning(f"Failed to parse command file {cmd_file}: {e}")

        return count

    def _parse_command_file(self, file_path: Path) -> AgentDescriptor | None:
        """
        Parse a command markdown file to extract agent metadata.

        Args:
            file_path: Path to the .md file

        Returns:
            AgentDescriptor or None if parsing fails
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract agent ID from filename
            # agent:risk.md -> risk
            agent_id = file_path.stem.replace("agent:", "")

            # Extract title and name from first header
            title_match = re.search(self.COMMAND_PATTERNS["title"], content, re.MULTILINE)
            if title_match:
                name = title_match.group(2).strip()
            else:
                # Fallback: capitalize agent_id
                name = agent_id.replace("-", " ").title() + " Agent"

            # Extract version
            version_match = re.search(self.COMMAND_PATTERNS["version"], content)
            version = version_match.group(1) if version_match else "1.0.0"

            # Extract description from Agent line or Domain line
            desc_match = re.search(self.COMMAND_PATTERNS["description"], content)
            domain_match = re.search(self.COMMAND_PATTERNS["domain"], content)

            if desc_match:
                description = desc_match.group(1).strip()
            elif domain_match:
                description = domain_match.group(1).strip()
            else:
                # Extract first paragraph after title
                description = self._extract_first_paragraph(content)

            # Determine category from content
            category = self._infer_category(agent_id, content)

            # Extract capabilities from "What This Agent Does" section
            capabilities = self._extract_capabilities(content)

            # Extract tags from content
            tags = self._extract_tags(agent_id, content)

            return AgentDescriptor(
                agent_id=agent_id,
                name=name,
                version=version,
                description=description,
                agent_type="command",
                category=category,
                capabilities=capabilities,
                tags=tags,
                command_path=str(file_path),
                command_name=f"/agent:{agent_id}",
                supports_parallel=True,
                supports_checkpoints=True,  # Commands can create checkpoints
                supports_sub_agents=False,  # Commands don't invoke sub-agents
                priority=50,  # Command agents have lower priority than Python
            )

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None

    def _extract_first_paragraph(self, content: str) -> str:
        """Extract first meaningful paragraph from markdown content."""
        lines = content.split("\n")
        paragraph_lines = []
        in_paragraph = False

        for line in lines:
            line = line.strip()
            # Skip headers and empty lines at start
            if not in_paragraph:
                if line and not line.startswith("#") and not line.startswith("*"):
                    in_paragraph = True
                    paragraph_lines.append(line)
            else:
                if not line:
                    break
                paragraph_lines.append(line)

        return " ".join(paragraph_lines)[:200] if paragraph_lines else "Command-based agent"

    def _infer_category(self, agent_id: str, content: str) -> AgentCategory:
        """Infer agent category from ID and content."""
        content_lower = content.lower()

        category_keywords = {
            AgentCategory.RESEARCH: ["research", "search", "precedent", "bge", "case law"],
            AgentCategory.STRATEGY: ["strategy", "litigation", "planning", "approach"],
            AgentCategory.DRAFTING: ["draft", "document", "template", "write"],
            AgentCategory.ANALYSIS: ["analysis", "assess", "evaluate", "risk", "score"],
            AgentCategory.COMPLIANCE: ["compliance", "regulatory", "gdpr", "data protection"],
            AgentCategory.SPECIALIZED: ["fiscal", "tax", "corporate", "realestate", "cantonal"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in agent_id.lower() or kw in content_lower for kw in keywords):
                return category

        return AgentCategory.UTILITY

    def _extract_capabilities(self, content: str) -> list[AgentCapability]:
        """Extract capabilities from markdown content."""
        capabilities = []

        # Look for "What This Agent Does" section
        match = re.search(
            r"##\s*What This (?:Agent|Command) Does\s*\n(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )

        if match:
            section = match.group(1)
            # Extract bullet points
            bullets = re.findall(r"[-*]\s+\*\*([^*]+)\*\*:\s*(.+)", section)
            for name, desc in bullets:
                capabilities.append(
                    AgentCapability(
                        name=name.lower().replace(" ", "_"),
                        description=desc.strip(),
                    )
                )

        return capabilities[:5]  # Limit to 5 capabilities

    def _extract_tags(self, agent_id: str, content: str) -> list[str]:
        """Extract relevant tags from content."""
        tags = [agent_id]

        # Add category-based tags
        tag_patterns = {
            "research": ["research", "bge", "precedent"],
            "risk": ["risk", "assessment", "probability"],
            "compliance": ["compliance", "regulatory", "gdpr"],
            "fiscal": ["tax", "fiscal", "steuer"],
            "corporate": ["corporate", "company", "gesellschaft"],
            "procedure": ["procedure", "prozess", "verfahren"],
            "cantonal": ["cantonal", "kanton"],
            "translator": ["translation", "language", "multilingual"],
            "citation": ["citation", "reference", "formatting"],
            "data-protection": ["data", "privacy", "dsg"],
            "realestate": ["property", "immobilien", "real estate"],
        }

        content_lower = content.lower()
        for _tag_group, keywords in tag_patterns.items():
            if any(kw in content_lower for kw in keywords):
                tags.extend(keywords[:2])

        return list(set(tags))[:10]

    def _build_indexes(self) -> None:
        """Build category and capability indexes."""
        for agent_id, descriptor in self._agents.items():
            # Index by category
            if descriptor.category not in self._by_category:
                self._by_category[descriptor.category] = []
            self._by_category[descriptor.category].append(agent_id)

            # Index by capability
            for cap in descriptor.capabilities:
                if cap.name not in self._by_capability:
                    self._by_capability[cap.name] = []
                self._by_capability[cap.name].append(agent_id)

    # =========================================================================
    # Public API
    # =========================================================================

    def get_agent(self, agent_id: str) -> AgentDescriptor | None:
        """
        Get an agent descriptor by ID.

        Args:
            agent_id: The agent identifier

        Returns:
            AgentDescriptor or None if not found
        """
        return self._agents.get(agent_id)

    def list_agents(self) -> list[AgentDescriptor]:
        """
        List all registered agents.

        Returns:
            List of all agent descriptors, sorted by priority
        """
        return sorted(self._agents.values(), key=lambda a: (a.priority, a.agent_id))

    def list_agent_ids(self) -> list[str]:
        """
        List all registered agent IDs.

        Returns:
            List of agent IDs
        """
        return sorted(self._agents.keys())

    def get_agents_by_category(self, category: AgentCategory) -> list[AgentDescriptor]:
        """
        Get all agents in a category.

        Args:
            category: The agent category

        Returns:
            List of matching agent descriptors
        """
        agent_ids = self._by_category.get(category, [])
        return [self._agents[aid] for aid in agent_ids]

    def get_agents_by_capability(self, capability: str) -> list[AgentDescriptor]:
        """
        Get agents with a specific capability.

        Args:
            capability: The capability name

        Returns:
            List of matching agent descriptors
        """
        agent_ids = self._by_capability.get(capability, [])
        return [self._agents[aid] for aid in agent_ids]

    def get_agents_by_tag(self, tag: str) -> list[AgentDescriptor]:
        """
        Get agents with a specific tag.

        Args:
            tag: The tag to search for

        Returns:
            List of matching agent descriptors
        """
        return [a for a in self._agents.values() if tag.lower() in [t.lower() for t in a.tags]]

    def get_agents_by_type(self, agent_type: Literal["python", "command"]) -> list[AgentDescriptor]:
        """
        Get agents by implementation type.

        Args:
            agent_type: "python" or "command"

        Returns:
            List of matching agent descriptors
        """
        return [a for a in self._agents.values() if a.agent_type == agent_type]

    def search_agents(self, query: str) -> list[AgentDescriptor]:
        """
        Search agents by query string.

        Searches across agent ID, name, description, and tags.

        Args:
            query: Search query

        Returns:
            List of matching agent descriptors
        """
        query_lower = query.lower()
        matches = []

        for descriptor in self._agents.values():
            score = 0

            # Exact ID match
            if query_lower == descriptor.agent_id.lower():
                score += 100

            # ID contains query
            if query_lower in descriptor.agent_id.lower():
                score += 50

            # Name contains query
            if query_lower in descriptor.name.lower():
                score += 30

            # Description contains query
            if query_lower in descriptor.description.lower():
                score += 20

            # Tag match
            if any(query_lower in tag.lower() for tag in descriptor.tags):
                score += 10

            if score > 0:
                matches.append((score, descriptor))

        # Sort by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches]

    def is_registered(self, agent_id: str) -> bool:
        """Check if an agent is registered."""
        return agent_id in self._agents

    def get_python_agents(self) -> list[AgentDescriptor]:
        """Get all Python-based agents."""
        return self.get_agents_by_type("python")

    def get_command_agents(self) -> list[AgentDescriptor]:
        """Get all command-based agents."""
        return self.get_agents_by_type("command")

    def __len__(self) -> int:
        """Return number of registered agents."""
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        """Check if agent is registered."""
        return agent_id in self._agents

    def __iter__(self) -> "Iterator[AgentDescriptor]":
        """Iterate over agent descriptors."""
        return iter(self._agents.values())

    def __repr__(self) -> str:
        """String representation."""
        python_count = len(self.get_python_agents())
        command_count = len(self.get_command_agents())
        return f"AgentRegistry(python={python_count}, command={command_count}, total={len(self)})"


# =============================================================================
# Global Registry Instance
# =============================================================================

# Singleton instance for convenience
_global_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    Creates and initializes the registry on first call.

    Returns:
        The global AgentRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def refresh_registry() -> AgentRegistry:
    """
    Refresh the global registry by re-discovering agents.

    Returns:
        The refreshed AgentRegistry instance
    """
    global _global_registry
    _global_registry = AgentRegistry()
    return _global_registry
