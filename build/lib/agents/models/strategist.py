"""
Strategist Agent Data Models

This module provides data models specific to the StrategistAgent for
litigation strategy development, risk assessment, and cost estimation.

Designed for Swiss legal practice with CHF currency and Swiss procedural context.

Strategiemodelle / Modèles stratégiques / Modelli strategici
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.agents.models.shared import Jurisdiction, Language, RiskLevel


class StrategyType(Enum):
    """
    Litigation strategy types for case handling.

    Strategietypen / Types de stratégie / Tipi di strategia:
        AGGRESSIVE: Forceful approach maximizing legal pressure
        DEFENSIVE: Protective approach minimizing exposure
        SETTLEMENT: Focus on negotiated resolution
        HYBRID: Combination approach adapting to circumstances
    """

    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    SETTLEMENT = "settlement"
    HYBRID = "hybrid"

    @property
    def description(self) -> dict[str, str]:
        """Return strategy description in multiple languages."""
        descriptions = {
            StrategyType.AGGRESSIVE: {
                "de": "Aggressive Strategie mit maximalem rechtlichen Druck",
                "fr": "Stratégie agressive avec pression juridique maximale",
                "it": "Strategia aggressiva con massima pressione legale",
                "en": "Aggressive strategy with maximum legal pressure",
            },
            StrategyType.DEFENSIVE: {
                "de": "Defensive Strategie zur Risikominimierung",
                "fr": "Stratégie défensive pour minimiser les risques",
                "it": "Strategia difensiva per minimizzare i rischi",
                "en": "Defensive strategy to minimize exposure",
            },
            StrategyType.SETTLEMENT: {
                "de": "Vergleichsorientierte Strategie",
                "fr": "Stratégie orientée vers le règlement",
                "it": "Strategia orientata all'accordo",
                "en": "Settlement-focused strategy",
            },
            StrategyType.HYBRID: {
                "de": "Hybride Strategie mit flexibler Anpassung",
                "fr": "Stratégie hybride avec adaptation flexible",
                "it": "Strategia ibrida con adattamento flessibile",
                "en": "Hybrid strategy with flexible adaptation",
            },
        }
        return descriptions[self]

    @property
    def requires_checkpoint(self) -> bool:
        """Determine if this strategy type requires checkpoint confirmation."""
        return self == StrategyType.AGGRESSIVE


class SuccessProbability(Enum):
    """
    Case success probability bands for strategic assessment.

    Erfolgswahrscheinlichkeit / Probabilité de succès / Probabilità di successo:
        EXCELLENT: >80% - Strong case with clear precedent
        GOOD: 60-80% - Favorable position with some uncertainty
        MODERATE: 40-60% - Balanced position, outcome uncertain
        CHALLENGING: 20-40% - Difficult position, uphill battle
        UNLIKELY: <20% - Poor prospects, consider alternatives
    """

    EXCELLENT = "excellent"  # >80%
    GOOD = "good"  # 60-80%
    MODERATE = "moderate"  # 40-60%
    CHALLENGING = "challenging"  # 20-40%
    UNLIKELY = "unlikely"  # <20%

    @property
    def probability_range(self) -> tuple[float, float]:
        """Return the probability range as (min, max) percentages."""
        ranges = {
            SuccessProbability.EXCELLENT: (0.80, 1.00),
            SuccessProbability.GOOD: (0.60, 0.80),
            SuccessProbability.MODERATE: (0.40, 0.60),
            SuccessProbability.CHALLENGING: (0.20, 0.40),
            SuccessProbability.UNLIKELY: (0.00, 0.20),
        }
        return ranges[self]

    @property
    def midpoint(self) -> float:
        """Return the midpoint probability for calculations."""
        min_val, max_val = self.probability_range
        return (min_val + max_val) / 2

    @classmethod
    def from_percentage(cls, percentage: float) -> "SuccessProbability":
        """Determine probability band from percentage (0-100 or 0-1)."""
        # Normalize to 0-1 range
        if percentage > 1:
            percentage = percentage / 100

        if percentage >= 0.80:
            return cls.EXCELLENT
        elif percentage >= 0.60:
            return cls.GOOD
        elif percentage >= 0.40:
            return cls.MODERATE
        elif percentage >= 0.20:
            return cls.CHALLENGING
        else:
            return cls.UNLIKELY


@dataclass
class RiskAssessment:
    """
    Comprehensive risk evaluation for litigation strategy.

    Risikobeurteilung / Évaluation des risques / Valutazione dei rischi

    Attributes:
        overall_level: Aggregate risk level
        litigation_risk: Risk of adverse judgment
        cost_risk: Risk of cost escalation
        reputation_risk: Risk to client reputation
        factors: Identified risk factors
        mitigations: Recommended mitigation strategies
        confidence_score: Confidence in assessment (0.0-1.0)
    """

    overall_level: RiskLevel
    litigation_risk: RiskLevel
    cost_risk: RiskLevel
    reputation_risk: RiskLevel
    factors: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)
    confidence_score: float = 0.0

    def __post_init__(self) -> None:
        """Validate confidence score range."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")

    @property
    def requires_checkpoint(self) -> bool:
        """Determine if this assessment requires checkpoint confirmation."""
        return self.overall_level.requires_checkpoint

    @property
    def weighted_score(self) -> float:
        """Calculate weighted risk score for comparison."""
        # Weights: litigation 50%, cost 30%, reputation 20%
        return (
            self.litigation_risk.numeric_score * 0.5
            + self.cost_risk.numeric_score * 0.3
            + self.reputation_risk.numeric_score * 0.2
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize risk assessment to dictionary."""
        return {
            "overall_level": self.overall_level.value,
            "litigation_risk": self.litigation_risk.value,
            "cost_risk": self.cost_risk.value,
            "reputation_risk": self.reputation_risk.value,
            "factors": self.factors,
            "mitigations": self.mitigations,
            "confidence_score": self.confidence_score,
            "weighted_score": self.weighted_score,
            "requires_checkpoint": self.requires_checkpoint,
        }


@dataclass
class CostEstimate:
    """
    Legal cost estimation in Swiss Francs (CHF).

    Kostenschätzung / Estimation des coûts / Stima dei costi

    Attributes:
        minimum_chf: Best-case cost scenario
        maximum_chf: Worst-case cost scenario
        most_likely_chf: Most probable cost
        breakdown: Itemized cost breakdown
        assumptions: Key assumptions underlying estimates
        court_costs: Estimated court fees
        expert_fees: Estimated expert witness fees
        recovery_potential: Potential cost recovery from opponent
    """

    minimum_chf: float
    maximum_chf: float
    most_likely_chf: float
    breakdown: dict[str, float] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    court_costs: float = 0.0
    expert_fees: float = 0.0
    recovery_potential: float = 0.0  # Potential recovery if successful

    def __post_init__(self) -> None:
        """Validate cost estimate consistency."""
        if self.minimum_chf > self.most_likely_chf:
            raise ValueError("Minimum cost cannot exceed most likely cost")
        if self.most_likely_chf > self.maximum_chf:
            raise ValueError("Most likely cost cannot exceed maximum cost")

    @property
    def cost_range(self) -> float:
        """Calculate the range between min and max costs."""
        return self.maximum_chf - self.minimum_chf

    @property
    def uncertainty_factor(self) -> float:
        """Calculate uncertainty as ratio of range to most likely cost."""
        if self.most_likely_chf == 0:
            return 0.0
        return self.cost_range / self.most_likely_chf

    @property
    def requires_checkpoint(self) -> bool:
        """Determine if cost estimate requires checkpoint (>50k CHF)."""
        return self.maximum_chf > 50000

    @property
    def net_cost_if_successful(self) -> float:
        """Calculate net cost if case is won (costs minus recovery)."""
        return self.most_likely_chf - self.recovery_potential

    def format_display(self, language: Language = Language.DE) -> str:
        """Format cost estimate for display."""
        templates = {
            Language.DE: "CHF {min:,.0f} - {max:,.0f} (wahrscheinlich: CHF {likely:,.0f})",
            Language.FR: "CHF {min:,.0f} - {max:,.0f} (probable: CHF {likely:,.0f})",
            Language.IT: "CHF {min:,.0f} - {max:,.0f} (probabile: CHF {likely:,.0f})",
            Language.EN: "CHF {min:,.0f} - {max:,.0f} (most likely: CHF {likely:,.0f})",
        }
        return templates[language].format(
            min=self.minimum_chf,
            max=self.maximum_chf,
            likely=self.most_likely_chf,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize cost estimate to dictionary."""
        return {
            "minimum_chf": self.minimum_chf,
            "maximum_chf": self.maximum_chf,
            "most_likely_chf": self.most_likely_chf,
            "breakdown": self.breakdown,
            "assumptions": self.assumptions,
            "court_costs": self.court_costs,
            "expert_fees": self.expert_fees,
            "recovery_potential": self.recovery_potential,
            "cost_range": self.cost_range,
            "uncertainty_factor": self.uncertainty_factor,
            "net_cost_if_successful": self.net_cost_if_successful,
        }


@dataclass
class OpponentProfile:
    """
    Profile of opposing party for strategic analysis.

    Gegnerprofil / Profil de l'adversaire / Profilo dell'avversario

    Attributes:
        name: Opponent name
        legal_representation: Known legal representation
        litigation_history: Known litigation patterns
        financial_capacity: Estimated financial resources
        settlement_tendency: Tendency to settle vs. litigate
        strengths: Identified opponent strengths
        weaknesses: Identified opponent weaknesses
    """

    name: str
    legal_representation: str | None = None
    litigation_history: list[str] = field(default_factory=list)
    financial_capacity: str | None = None  # "low", "medium", "high", "unknown"
    settlement_tendency: str | None = None  # "likely", "unlikely", "unknown"
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize opponent profile to dictionary."""
        return {
            "name": self.name,
            "legal_representation": self.legal_representation,
            "litigation_history": self.litigation_history,
            "financial_capacity": self.financial_capacity,
            "settlement_tendency": self.settlement_tendency,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "notes": self.notes,
        }


@dataclass
class TimelineEvent:
    """
    Single event in a litigation timeline.

    Attributes:
        date: Event date or expected date
        event: Event description
        is_deadline: Whether this is a hard deadline
        dependencies: Events that must complete before this one
        responsible: Party responsible for this event
    """

    date: str | None  # ISO format or "TBD"
    event: str
    is_deadline: bool = False
    dependencies: list[str] = field(default_factory=list)
    responsible: str = "client"  # client, opponent, court


@dataclass
class StrategyRecommendation:
    """
    Complete strategy recommendation output from StrategistAgent.

    Strategieempfehlung / Recommandation stratégique / Raccomandazione strategica

    Attributes:
        strategy_type: Recommended strategy approach
        success_probability: Estimated probability of success
        risk_assessment: Comprehensive risk evaluation
        cost_estimate: Cost projections
        recommended_actions: Prioritized list of recommended actions
        alternative_strategies: Alternative approaches with trade-offs
        key_arguments: Main legal arguments to advance
        weak_points: Vulnerabilities to address
        timeline_weeks: Estimated timeline in weeks
        checkpoints: Recommended review checkpoints
        opponent_profile: Analysis of opposing party (if available)
    """

    strategy_type: StrategyType
    success_probability: SuccessProbability
    risk_assessment: RiskAssessment
    cost_estimate: CostEstimate
    recommended_actions: list[str] = field(default_factory=list)
    alternative_strategies: list[dict[str, Any]] = field(default_factory=list)
    key_arguments: list[str] = field(default_factory=list)
    weak_points: list[str] = field(default_factory=list)
    timeline_weeks: int = 0
    timeline_events: list[TimelineEvent] = field(default_factory=list)
    checkpoints: list[str] = field(default_factory=list)
    opponent_profile: OpponentProfile | None = None
    jurisdiction: Jurisdiction = Jurisdiction.FEDERAL
    language: Language = Language.DE
    created_at: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0

    @property
    def requires_checkpoint(self) -> bool:
        """Determine if this recommendation requires checkpoint confirmation."""
        return (
            self.strategy_type.requires_checkpoint
            or self.risk_assessment.requires_checkpoint
            or self.cost_estimate.requires_checkpoint
        )

    @property
    def expected_value(self) -> float:
        """Calculate expected value (success probability * potential recovery - costs)."""
        recovery = self.cost_estimate.recovery_potential
        prob = self.success_probability.midpoint
        cost = self.cost_estimate.most_likely_chf
        return (recovery * prob) - cost

    def to_dict(self) -> dict[str, Any]:
        """Serialize strategy recommendation to dictionary."""
        return {
            "strategy_type": self.strategy_type.value,
            "success_probability": self.success_probability.value,
            "risk_assessment": self.risk_assessment.to_dict(),
            "cost_estimate": self.cost_estimate.to_dict(),
            "recommended_actions": self.recommended_actions,
            "alternative_strategies": self.alternative_strategies,
            "key_arguments": self.key_arguments,
            "weak_points": self.weak_points,
            "timeline_weeks": self.timeline_weeks,
            "checkpoints": self.checkpoints,
            "opponent_profile": (
                self.opponent_profile.to_dict() if self.opponent_profile else None
            ),
            "jurisdiction": self.jurisdiction.value,
            "language": self.language.value,
            "created_at": self.created_at.isoformat(),
            "confidence_score": self.confidence_score,
            "requires_checkpoint": self.requires_checkpoint,
            "expected_value": self.expected_value,
        }

    def get_summary(self, language: Language = Language.DE) -> str:
        """Generate executive summary in specified language."""
        templates = {
            Language.DE: """
Strategieempfehlung: {strategy}
Erfolgswahrscheinlichkeit: {probability}
Gesamtrisiko: {risk}
Geschätzte Kosten: {costs}
Zeitrahmen: {timeline} Wochen
            """,
            Language.FR: """
Recommandation stratégique: {strategy}
Probabilité de succès: {probability}
Risque global: {risk}
Coûts estimés: {costs}
Délai: {timeline} semaines
            """,
            Language.IT: """
Raccomandazione strategica: {strategy}
Probabilità di successo: {probability}
Rischio complessivo: {risk}
Costi stimati: {costs}
Tempistica: {timeline} settimane
            """,
            Language.EN: """
Strategy Recommendation: {strategy}
Success Probability: {probability}
Overall Risk: {risk}
Estimated Costs: {costs}
Timeline: {timeline} weeks
            """,
        }

        return (
            templates[language]
            .format(
                strategy=self.strategy_type.description[language.value],
                probability=self.success_probability.value,
                risk=self.risk_assessment.overall_level.value,
                costs=self.cost_estimate.format_display(language),
                timeline=self.timeline_weeks,
            )
            .strip()
        )
