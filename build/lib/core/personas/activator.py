"""
Persona Activation Framework for BetterCallClaude v2.0

This module provides context-based persona activation to inject legal expert
capabilities into Claude Code conversations.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PersonaCategory(Enum):
    """Categories of legal expert personas"""

    LEGAL_RESEARCH = "legal_research"
    SWISS_LAW = "swiss_law"
    DRAFTING = "drafting"
    LITIGATION = "litigation"
    COMPLIANCE = "compliance"
    CORPORATE = "corporate"


@dataclass
class PersonaSpec:
    """Specification for a legal expert persona"""

    persona_id: str
    name: str
    category: PersonaCategory
    description: str
    expertise_areas: list[str]
    prompt_template: str
    mcp_servers: list[str]
    priority: int = 0  # Higher priority personas activated first


class PersonaActivator:
    """
    Manages activation of legal expert personas based on context

    Features:
    - Context-based persona selection
    - Multi-persona coordination
    - Persona priority management
    - Prompt template injection
    - MCP server coordination

    Example:
        activator = PersonaActivator()

        # Register persona
        activator.register_persona(
            persona_id="legal_researcher",
            name="Legal Research Specialist",
            category=PersonaCategory.LEGAL_RESEARCH,
            expertise_areas=["BGE search", "precedent analysis"],
            prompt_template="You are a Swiss legal research specialist..."
        )

        # Activate persona for command
        personas = activator.activate_for_command("legal:research")

        # Get combined prompt
        prompt = activator.get_combined_prompt(personas)
    """

    def __init__(self, persona_dir: Path | None = None) -> None:
        """
        Initialize persona activator

        Args:
            persona_dir: Directory containing persona specification files
                        (default: ./.claude/personas/)
        """
        if persona_dir is None:
            persona_dir = Path.cwd() / ".claude" / "personas"

        self.persona_dir = Path(persona_dir)
        self._personas: dict[str, PersonaSpec] = {}
        self._command_personas: dict[str, list[str]] = {}
        self._active_personas: set[str] = set()

    def register_persona(
        self,
        persona_id: str,
        name: str,
        category: PersonaCategory,
        description: str,
        expertise_areas: list[str],
        prompt_template: str,
        mcp_servers: list[str] | None = None,
        priority: int = 0,
    ) -> None:
        """
        Register a legal expert persona

        Args:
            persona_id: Unique persona identifier
            name: Human-readable persona name
            category: Persona category
            description: Persona description
            expertise_areas: List of expertise areas
            prompt_template: Prompt template for persona injection
            mcp_servers: Required MCP servers (optional)
            priority: Activation priority (higher = earlier)
        """
        persona = PersonaSpec(
            persona_id=persona_id,
            name=name,
            category=category,
            description=description,
            expertise_areas=expertise_areas,
            prompt_template=prompt_template,
            mcp_servers=mcp_servers or [],
            priority=priority,
        )

        self._personas[persona_id] = persona
        logger.info(f"Registered persona: {persona_id} ({name})")

    def register_command_personas(self, command_name: str, persona_ids: list[str]) -> None:
        """
        Register personas to auto-activate for specific command

        Args:
            command_name: Command name (e.g., "legal:research")
            persona_ids: List of persona IDs to activate
        """
        self._command_personas[command_name] = persona_ids
        logger.info(f"Registered {len(persona_ids)} personas for command: {command_name}")

    def activate_persona(self, persona_id: str) -> bool:
        """
        Manually activate a persona

        Args:
            persona_id: Persona identifier to activate

        Returns:
            True if persona was activated, False if not found

        Raises:
            ValueError: If persona not registered
        """
        if persona_id not in self._personas:
            raise ValueError(f"Persona '{persona_id}' not registered")

        self._active_personas.add(persona_id)
        logger.info(f"Activated persona: {persona_id}")
        return True

    def deactivate_persona(self, persona_id: str) -> bool:
        """
        Deactivate a persona

        Args:
            persona_id: Persona identifier to deactivate

        Returns:
            True if persona was deactivated, False if wasn't active
        """
        if persona_id in self._active_personas:
            self._active_personas.remove(persona_id)
            logger.info(f"Deactivated persona: {persona_id}")
            return True
        return False

    def activate_for_command(self, command_name: str) -> list[PersonaSpec]:
        """
        Activate personas registered for specific command

        Args:
            command_name: Command name to activate personas for

        Returns:
            List of activated PersonaSpec objects, sorted by priority
        """
        if command_name not in self._command_personas:
            return []

        persona_ids = self._command_personas[command_name]
        activated = []

        for persona_id in persona_ids:
            if persona_id in self._personas:
                self.activate_persona(persona_id)
                activated.append(self._personas[persona_id])

        # Sort by priority (higher first)
        activated.sort(key=lambda p: p.priority, reverse=True)

        logger.info(f"Activated {len(activated)} personas for command: {command_name}")
        return activated

    def get_active_personas(self) -> list[PersonaSpec]:
        """
        Get all currently active personas

        Returns:
            List of active PersonaSpec objects, sorted by priority
        """
        active = [self._personas[pid] for pid in self._active_personas if pid in self._personas]

        # Sort by priority (higher first)
        active.sort(key=lambda p: p.priority, reverse=True)
        return active

    def get_combined_prompt(self, personas: list[PersonaSpec] | None = None) -> str:
        """
        Generate combined prompt from active personas

        Args:
            personas: List of personas to include (default: all active)

        Returns:
            Combined prompt template string
        """
        if personas is None:
            personas = self.get_active_personas()

        if not personas:
            return ""

        prompt_parts = [
            "# Active Legal Expert Personas\n",
            "The following legal expert personas are active for this session:\n",
        ]

        for persona in personas:
            prompt_parts.append(f"\n## {persona.name} ({persona.persona_id})")
            prompt_parts.append(f"\n**Category**: {persona.category.value}")
            prompt_parts.append(f"\n**Expertise**: {', '.join(persona.expertise_areas)}")
            prompt_parts.append(f"\n\n{persona.prompt_template}\n")

        return "\n".join(prompt_parts)

    def get_required_mcp_servers(self, personas: list[PersonaSpec] | None = None) -> list[str]:
        """
        Get list of MCP servers required by active personas

        Args:
            personas: List of personas to check (default: all active)

        Returns:
            Deduplicated list of required MCP server IDs
        """
        if personas is None:
            personas = self.get_active_personas()

        mcp_servers = set()
        for persona in personas:
            mcp_servers.update(persona.mcp_servers)

        return sorted(mcp_servers)

    def clear_all(self) -> None:
        """Deactivate all personas"""
        self._active_personas.clear()
        logger.info("Cleared all active personas")

    def load_personas_from_directory(self) -> int:
        """
        Load persona specifications from persona directory

        Returns:
            Number of personas loaded

        Note:
            This is a placeholder for future implementation.
            Personas will be loaded from .claude/personas/ directory
            in a structured format (YAML or JSON).
        """
        # TODO: Implement persona loading from files
        # For now, register some default personas programmatically

        self.register_persona(
            persona_id="legal_researcher",
            name="Legal Research Specialist",
            category=PersonaCategory.LEGAL_RESEARCH,
            description=(
                "Expert in Swiss legal research, BGE precedent analysis, "
                "and statutory interpretation"
            ),
            expertise_areas=[
                "BGE search",
                "Precedent analysis",
                "Citation validation",
                "Legal source evaluation",
            ],
            prompt_template=(
                "You are a Swiss legal research specialist with deep expertise in:\n"
                "- BGE (Bundesgerichtsentscheide) precedent analysis\n"
                "- Federal and cantonal statutory research\n"
                "- Legal citation formats and validation\n"
                "- Multi-lingual legal sources (DE/FR/IT)\n\n"
                "When conducting legal research, always:\n"
                "1. Validate citation formats (BGE format: [Volume] [Chamber] [Page])\n"
                "2. Consider federal-cantonal hierarchy\n"
                "3. Check for overruling or distinguishing precedents\n"
                "4. Note language of original decision"
            ),
            mcp_servers=["bge_search", "entscheidsuche"],
            priority=100,
        )

        self.register_persona(
            persona_id="swiss_law_expert",
            name="Swiss Law Expert",
            category=PersonaCategory.SWISS_LAW,
            description=(
                "Expert in Swiss legal system structure, federal-cantonal "
                "hierarchy, and multi-lingual legal reasoning"
            ),
            expertise_areas=[
                "Federal law",
                "Cantonal law",
                "Legal system structure",
                "Multi-lingual reasoning",
            ],
            prompt_template=(
                "You are a Swiss law expert with comprehensive knowledge of:\n"
                "- Federal-cantonal legal hierarchy\n"
                "- 26 cantonal legal systems\n"
                "- Court hierarchy (Federal Supreme Court → Cantonal → District)\n"
                "- Multi-lingual legal reasoning (DE/FR/IT/RM)\n\n"
                "When analyzing Swiss law, always:\n"
                "1. Consider federal vs cantonal jurisdiction\n"
                "2. Note language region implications\n"
                "3. Check for cantonal variations\n"
                "4. Respect legal hierarchy (federal > cantonal)"
            ),
            mcp_servers=["cantonal_courts", "legal_citations"],
            priority=90,
        )

        logger.info("Loaded 2 default personas")
        return 2

    def get_persona_stats(self) -> dict[str, Any]:
        """
        Get statistics about registered and active personas

        Returns:
            Dict with persona statistics
        """
        return {
            "total_registered": len(self._personas),
            "total_active": len(self._active_personas),
            "by_category": {
                category.value: sum(1 for p in self._personas.values() if p.category == category)
                for category in PersonaCategory
            },
            "active_persona_ids": sorted(self._active_personas),
        }
