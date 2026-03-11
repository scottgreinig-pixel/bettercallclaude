"""
JudicialReport data structure for adversarial workflow system.

This module defines the schema for judicial synthesis reports in the three-agent
architecture for Swiss legal analysis. The JudicialReport synthesizes advocate
and adversary positions with risk assessment and legal conclusions.

YAML Schema:
    synthesis:
      balanced_analysis: str (min 20 chars)
      convergent_points: List[str]
      divergent_points: List[str]
    risk_assessment:
      favorable_probability: float (0.0-1.0)
      unfavorable_probability: float (0.0-1.0, sum with favorable ±0.05 tolerance)
      confidence_level: float (0.0-1.0)
    legal_conclusion:
      primary_outcome: str (min 20 chars)
      alternative_outcomes: List[str]
"""

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class Synthesis:
    """
    Synthesis of advocate and adversary positions.

    Attributes:
        balanced_analysis: Objective analysis balancing both positions (min 20 chars)
        convergent_points: Areas where both positions agree
        divergent_points: Areas where positions disagree
    """

    balanced_analysis: str
    convergent_points: list[str] = field(default_factory=list)
    divergent_points: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate synthesis after initialization."""
        # Validate balanced_analysis
        if not self.balanced_analysis:
            raise ValueError("balanced_analysis cannot be empty")

        if not self.balanced_analysis.strip():
            raise ValueError("balanced_analysis cannot be whitespace only")

        if len(self.balanced_analysis) < 20:
            raise ValueError(
                f"balanced_analysis must be at least 20 characters, "
                f"got {len(self.balanced_analysis)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert synthesis to dictionary for YAML serialization."""
        return {
            "balanced_analysis": self.balanced_analysis,
            "convergent_points": self.convergent_points,
            "divergent_points": self.divergent_points,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Synthesis":
        """Create Synthesis from dictionary."""
        return cls(
            balanced_analysis=data["balanced_analysis"],
            convergent_points=data.get("convergent_points", []),
            divergent_points=data.get("divergent_points", []),
        )


@dataclass
class RiskAssessment:
    """
    Risk assessment of case outcome probabilities.

    Attributes:
        favorable_probability: Probability of favorable outcome (0.0-1.0)
        unfavorable_probability: Probability of unfavorable outcome (0.0-1.0)
        confidence_level: Confidence in the assessment (0.0-1.0)
    """

    favorable_probability: float
    unfavorable_probability: float
    confidence_level: float

    def __post_init__(self) -> None:
        """Validate risk assessment after initialization."""
        # Validate favorable_probability range
        if not (0.0 <= self.favorable_probability <= 1.0):
            raise ValueError(
                f"favorable_probability must be between 0.0 and 1.0, "
                f"got {self.favorable_probability}"
            )

        # Validate unfavorable_probability range
        if not (0.0 <= self.unfavorable_probability <= 1.0):
            raise ValueError(
                f"unfavorable_probability must be between 0.0 and 1.0, "
                f"got {self.unfavorable_probability}"
            )

        # Validate confidence_level range
        if not (0.0 <= self.confidence_level <= 1.0):
            raise ValueError(
                f"confidence_level must be between 0.0 and 1.0, got {self.confidence_level}"
            )

        # Validate probabilities sum to 1.0 within ±0.05 tolerance
        prob_sum = self.favorable_probability + self.unfavorable_probability
        if abs(prob_sum - 1.0) > 0.05:
            raise ValueError(
                f"favorable_probability and unfavorable_probability "
                f"must sum to 1.0 (±0.05 tolerance), got {prob_sum}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert risk assessment to dictionary for YAML serialization."""
        return {
            "favorable_probability": self.favorable_probability,
            "unfavorable_probability": self.unfavorable_probability,
            "confidence_level": self.confidence_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskAssessment":
        """Create RiskAssessment from dictionary."""
        return cls(
            favorable_probability=data["favorable_probability"],
            unfavorable_probability=data["unfavorable_probability"],
            confidence_level=data["confidence_level"],
        )


@dataclass
class LegalConclusion:
    """
    Legal conclusion from judicial synthesis.

    Attributes:
        primary_outcome: Primary legal conclusion (min 20 chars)
        alternative_outcomes: Alternative possible outcomes
    """

    primary_outcome: str
    alternative_outcomes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate legal conclusion after initialization."""
        # Validate primary_outcome
        if not self.primary_outcome:
            raise ValueError("primary_outcome cannot be empty")

        if not self.primary_outcome.strip():
            raise ValueError("primary_outcome cannot be whitespace only")

        if len(self.primary_outcome) < 20:
            raise ValueError(
                f"primary_outcome must be at least 20 characters, got {len(self.primary_outcome)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert legal conclusion to dictionary for YAML serialization."""
        return {
            "primary_outcome": self.primary_outcome,
            "alternative_outcomes": self.alternative_outcomes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LegalConclusion":
        """Create LegalConclusion from dictionary."""
        return cls(
            primary_outcome=data["primary_outcome"],
            alternative_outcomes=data.get("alternative_outcomes", []),
        )


@dataclass
class JudicialReport:
    """
    Judicial report synthesizing advocate and adversary positions.

    The JudicialReport represents the output of the Judge agent in the
    three-agent adversarial workflow system. It provides balanced synthesis,
    risk assessment, and legal conclusions.

    Attributes:
        synthesis: Balanced analysis of both positions
        risk_assessment: Probability assessment of outcomes
        legal_conclusion: Final legal conclusions and recommendations
    """

    synthesis: Synthesis
    risk_assessment: RiskAssessment
    legal_conclusion: LegalConclusion

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for YAML serialization."""
        return {
            "synthesis": self.synthesis.to_dict(),
            "risk_assessment": self.risk_assessment.to_dict(),
            "legal_conclusion": self.legal_conclusion.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JudicialReport":
        """Create JudicialReport from dictionary."""
        return cls(
            synthesis=Synthesis.from_dict(data["synthesis"]),
            risk_assessment=RiskAssessment.from_dict(data["risk_assessment"]),
            legal_conclusion=LegalConclusion.from_dict(data["legal_conclusion"]),
        )

    def to_yaml(self) -> str:
        """Convert report to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "JudicialReport":
        """Create JudicialReport from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
