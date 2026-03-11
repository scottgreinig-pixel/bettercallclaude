"""
AdversaryReport data structure for adversarial workflow system.

This module defines the schema for adversary agent reports in the three-agent
architecture for Swiss legal analysis. The AdversaryReport contains the strongest
anti-position arguments, opposing precedents, and legal citations.

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

Note: AdversaryReport uses the same Argument and Citation classes as AdvocateReport.
The only structural difference is semantic - adversary reports typically use position="anti".
"""

from dataclasses import dataclass, field
from typing import Any, Literal

import yaml

# Import shared classes from AdvocateReport
from adversarial_workflow.data_structures.advocate_report import Argument, Citation


@dataclass
class AdversaryReport:
    """
    Adversary agent report containing anti-position arguments.

    The AdversaryReport represents the output of the Adversary agent in the
    three-agent adversarial workflow system. It uses the same structure as
    AdvocateReport but typically contains position="anti" arguments.

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
    def from_dict(cls, data: dict[str, Any]) -> "AdversaryReport":
        """Create AdversaryReport from dictionary."""
        return cls(
            position=data["position"],
            arguments=[Argument.from_dict(arg) for arg in data.get("arguments", [])],
            citations=[Citation.from_dict(cit) for cit in data.get("citations", [])],
        )

    def to_yaml(self) -> str:
        """Convert report to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "AdversaryReport":
        """Create AdversaryReport from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
