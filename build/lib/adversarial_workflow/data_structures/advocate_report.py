"""
AdvocateReport data structure for adversarial workflow system.

This module defines the schema for advocate agent reports in the three-agent
architecture for Swiss legal analysis. The AdvocateReport contains the strongest
pro-position arguments, supporting precedents, and legal citations.

YAML Schema:
    position: "pro" | "anti"
    arguments:
      - argument_id: str
        statutory_basis: List[str]
        precedents: List[str]
        reasoning: str (min 20 chars)
        strength: float (0.0-1.0)
    citations:
      - citation_id: str
        type: "bge" | "statute" | "doctrine"
        reference: str
        verified: bool
"""

from dataclasses import dataclass, field
from typing import Any, Literal

import yaml


@dataclass
class Argument:
    """
    Legal argument supporting advocate's position.

    Attributes:
        argument_id: Unique identifier for the argument
        statutory_basis: List of statutory provisions supporting argument
        precedents: List of BGE/court decisions supporting argument
        reasoning: Textual explanation of the legal reasoning (min 20 chars)
        strength: Assessed strength of argument (0.0 = weak, 1.0 = strong)
    """

    argument_id: str
    statutory_basis: list[str] = field(default_factory=list)
    precedents: list[str] = field(default_factory=list)
    reasoning: str = ""
    strength: float = 0.5

    def __post_init__(self) -> None:
        """Validate argument after initialization."""
        # Validate argument_id
        if not self.argument_id:
            raise ValueError("argument_id cannot be empty")

        if not self.argument_id.strip():
            raise ValueError("argument_id cannot be whitespace only")

        # Validate reasoning
        if not self.reasoning:
            raise ValueError("reasoning cannot be empty")

        if not self.reasoning.strip():
            raise ValueError("reasoning cannot be whitespace only")

        if len(self.reasoning) < 20:
            raise ValueError(f"reasoning must be at least 20 characters, got {len(self.reasoning)}")

        # Validate strength
        if not (0.0 <= self.strength <= 1.0):
            raise ValueError(f"strength must be between 0.0 and 1.0, got {self.strength}")

    def to_dict(self) -> dict[str, Any]:
        """Convert argument to dictionary for YAML serialization."""
        return {
            "argument_id": self.argument_id,
            "statutory_basis": self.statutory_basis,
            "precedents": self.precedents,
            "reasoning": self.reasoning,
            "strength": self.strength,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Argument":
        """Create Argument from dictionary."""
        return cls(
            argument_id=data["argument_id"],
            statutory_basis=data.get("statutory_basis", []),
            precedents=data.get("precedents", []),
            reasoning=data["reasoning"],
            strength=data["strength"],
        )


@dataclass
class Citation:
    """
    Legal citation referenced in advocate report.

    Attributes:
        citation_id: Unique identifier for the citation
        type: Type of citation (bge, statute, doctrine)
        reference: Full citation reference string
        verified: Whether citation has been verified for accuracy
    """

    citation_id: str
    type: Literal["bge", "statute", "doctrine"]
    reference: str
    verified: bool = False

    def __post_init__(self) -> None:
        """Validate citation after initialization."""
        # Validate citation_id
        if not self.citation_id:
            raise ValueError("citation_id cannot be empty")

        if not self.citation_id.strip():
            raise ValueError("citation_id cannot be whitespace only")

        # Validate reference
        if not self.reference:
            raise ValueError("reference cannot be empty")

        if not self.reference.strip():
            raise ValueError("reference cannot be whitespace only")

    def to_dict(self) -> dict[str, Any]:
        """Convert citation to dictionary for YAML serialization."""
        return {
            "citation_id": self.citation_id,
            "type": self.type,
            "reference": self.reference,
            "verified": self.verified,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Citation":
        """Create Citation from dictionary."""
        return cls(
            citation_id=data["citation_id"],
            type=data["type"],
            reference=data["reference"],
            verified=data.get("verified", False),
        )


@dataclass
class AdvocateReport:
    """
    Advocate agent report containing pro/anti position arguments.

    The AdvocateReport represents the output of either the Advocate or Adversary
    agent in the three-agent adversarial workflow system.

    Attributes:
        position: Position of the report ("pro" or "anti")
        arguments: List of legal arguments supporting the position
        citations: List of legal citations referenced in arguments
    """

    position: Literal["pro", "anti"]
    arguments: list[Argument] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate report after initialization."""
        # Validate at least one argument is provided
        if not self.arguments:
            raise ValueError("At least one argument is required")

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for YAML serialization."""
        return {
            "position": self.position,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "citations": [cit.to_dict() for cit in self.citations],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AdvocateReport":
        """Create AdvocateReport from dictionary."""
        return cls(
            position=data["position"],
            arguments=[Argument.from_dict(arg) for arg in data.get("arguments", [])],
            citations=[Citation.from_dict(cit) for cit in data.get("citations", [])],
        )

    def to_yaml(self) -> str:
        """Convert report to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "AdvocateReport":
        """Create AdvocateReport from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
