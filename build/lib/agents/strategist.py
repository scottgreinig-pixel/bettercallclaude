"""
BetterCallClaude Strategist Agent

Legal strategy development agent for Swiss law litigation.
Provides comprehensive litigation strategy analysis including risk assessment,
cost-benefit analysis, and opponent profiling.

Workflow:
1. ANALYZE - Parse case facts, identify legal issues
2. ASSESS - Risk evaluation across multiple dimensions
3. ESTIMATE - Cost projections with CHF calculations
4. STRATEGIZE - Develop and recommend strategy
5. REVIEW - Checkpoint for high-risk strategies
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .base import (
    ActionType,
    AgentBase,
    AgentOutcome,
    AgentResult,
    AutonomyMode,
)
from .models.shared import (
    CaseFacts,
    Jurisdiction,
    Language,
    RiskLevel,
)
from .models.strategist import (
    CostEstimate,
    OpponentProfile,
    RiskAssessment,
    StrategyRecommendation,
    StrategyType,
    SuccessProbability,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Strategy-Specific Data Classes
# =============================================================================


@dataclass
class CaseAnalysis:
    """Results of case facts analysis."""

    case_id: str
    legal_issues: list[str]
    key_facts: list[str]
    disputed_matters: list[str]
    evidence_assessment: dict[str, str]
    jurisdictional_analysis: dict[str, Any]
    preliminary_position: str
    confidence_score: float


@dataclass
class StrategistDeliverable:
    """
    Complete deliverable from StrategistAgent.

    Contains full strategy recommendation with supporting analysis.
    """

    recommendation: StrategyRecommendation
    case_analysis: CaseAnalysis
    alternative_strategies: list[dict[str, Any]]
    next_steps: list[str]
    warnings: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize deliverable to dictionary."""
        return {
            "recommendation": self.recommendation.to_dict(),
            "case_analysis": {
                "case_id": self.case_analysis.case_id,
                "legal_issues": self.case_analysis.legal_issues,
                "key_facts": self.case_analysis.key_facts,
                "disputed_matters": self.case_analysis.disputed_matters,
                "preliminary_position": self.case_analysis.preliminary_position,
                "confidence_score": self.case_analysis.confidence_score,
            },
            "alternative_strategies": self.alternative_strategies,
            "next_steps": self.next_steps,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


# =============================================================================
# Checkpoint Configuration
# =============================================================================


STRATEGY_CHECKPOINTS = {
    "risk_high": {
        "trigger": "risk_assessment.overall_level in [HIGH, VERY_HIGH]",
        "message_de": "⚠️ Hohe Risikowarnung: Strategie erfordert Bestätigung.",
        "message_fr": "⚠️ Alerte risque élevé: La stratégie nécessite confirmation.",
        "message_it": "⚠️ Avviso rischio elevato: La strategia richiede conferma.",
        "message_en": "⚠️ High-risk strategy identified. Review before proceeding.",
        "requires_confirmation": True,
    },
    "cost_significant": {
        "trigger": "cost_estimate.maximum_chf > 50000",
        "message_de": "💰 Erhebliche Kosten: Budgetgenehmigung empfohlen.",
        "message_fr": "💰 Coûts importants: Approbation du budget recommandée.",
        "message_it": "💰 Costi significativi: Approvazione del budget raccomandata.",
        "message_en": "💰 Significant cost projection. Confirm budget approval.",
        "requires_confirmation": True,
    },
    "strategy_aggressive": {
        "trigger": "strategy_type == AGGRESSIVE",
        "message_de": "⚔️ Aggressive Strategie gewählt. Bestätigen Sie den Ansatz.",
        "message_fr": "⚔️ Stratégie agressive sélectionnée. Confirmez l'approche.",
        "message_it": "⚔️ Strategia aggressiva selezionata. Confermare l'approccio.",
        "message_en": "⚔️ Aggressive strategy selected. Confirm approach.",
        "requires_confirmation": True,
    },
}


# =============================================================================
# Strategist Agent
# =============================================================================


class StrategistAgent(AgentBase):
    """
    Litigation strategy development agent for Swiss law.

    Analyzes case facts, assesses risks, estimates costs, and develops
    comprehensive litigation strategies with proper checkpoints for
    high-risk recommendations.

    Supports DE/FR/IT/EN languages and all Swiss jurisdictions.
    """

    WORKFLOW_STEPS = [
        "ANALYZE",  # Parse case facts, identify legal issues
        "ASSESS",  # Comprehensive risk evaluation
        "ESTIMATE",  # Cost-benefit analysis
        "STRATEGIZE",  # Develop strategy recommendation
        "REVIEW",  # Final review with checkpoints
    ]

    # Swiss court cost tables (approximate, by streitwert ranges)
    COURT_COST_TABLES = {
        Jurisdiction.FEDERAL: {
            (0, 30000): (800, 5000),
            (30000, 100000): (2000, 12000),
            (100000, 500000): (5000, 30000),
            (500000, float("inf")): (10000, 100000),
        },
        Jurisdiction.ZH: {
            (0, 30000): (600, 4000),
            (30000, 100000): (1500, 10000),
            (100000, 500000): (4000, 25000),
            (500000, float("inf")): (8000, 80000),
        },
        # Default for other cantons
        "default": {
            (0, 30000): (700, 4500),
            (30000, 100000): (1800, 11000),
            (100000, 500000): (4500, 27000),
            (500000, float("inf")): (9000, 90000),
        },
    }

    # Hourly rates by seniority (CHF)
    ATTORNEY_RATES = {
        "partner": (450, 650),
        "senior_associate": (350, 450),
        "associate": (250, 350),
        "paralegal": (150, 200),
    }

    @property
    def agent_id(self) -> str:
        return "strategist"

    @property
    def agent_version(self) -> str:
        return "1.0.0"

    async def execute(
        self,
        task: str,
        case_facts: CaseFacts | None = None,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        language: Language = Language.DE,
        research_findings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AgentResult[StrategistDeliverable]:
        """
        Execute strategy development workflow.

        Args:
            task: Strategy development request description
            case_facts: Structured case facts for analysis
            jurisdiction: Target jurisdiction
            language: Output language
            research_findings: Optional research from ResearcherAgent

        Returns:
            AgentResult containing StrategistDeliverable
        """
        self._start_time = datetime.utcnow()
        logger.info(f"StrategistAgent starting: {task}")

        try:
            # Create initial checkpoint
            self.create_checkpoint("auto", "Strategy analysis started")

            # Step 1: ANALYZE case facts
            self.update_state("step", "ANALYZE")
            analysis = await self.analyze_case(case_facts or CaseFacts(summary=task))
            self._record_action(
                ActionType.ANALYZE,
                "Case analysis completed",
                inputs={"task": task},
                outputs={"issues_found": len(analysis.legal_issues)},
                duration_ms=100,
            )

            # Step 2: ASSESS risk
            self.update_state("step", "ASSESS")
            risk_assessment = await self.assess_risk(analysis, jurisdiction)
            self._record_action(
                ActionType.ANALYZE,
                "Risk assessment completed",
                inputs={"case_id": analysis.case_id},
                outputs={"risk_level": risk_assessment.overall_level.value},
                duration_ms=100,
            )

            # Check for high-risk checkpoint
            if risk_assessment.requires_checkpoint:
                checkpoint_msg = str(STRATEGY_CHECKPOINTS["risk_high"][f"message_{language.value}"])
                if self.autonomy_mode != AutonomyMode.AUTONOMOUS:
                    self.create_checkpoint("user", checkpoint_msg)
                    await self.request_user_confirmation(checkpoint_msg)

            # Step 3: ESTIMATE costs
            self.update_state("step", "ESTIMATE")
            strategy_type = self._determine_initial_strategy(analysis, risk_assessment)
            dispute_value = case_facts.value_in_dispute if case_facts else None
            cost_estimate = await self.estimate_costs(
                strategy_type,
                jurisdiction,
                dispute_value if dispute_value is not None else 100000.0,
            )
            self._record_action(
                ActionType.ANALYZE,
                "Cost estimation completed",
                inputs={"strategy_type": strategy_type.value},
                outputs={"estimated_cost_chf": cost_estimate.most_likely_chf},
                duration_ms=100,
            )

            # Check for significant cost checkpoint
            if cost_estimate.requires_checkpoint:
                checkpoint_msg = str(
                    STRATEGY_CHECKPOINTS["cost_significant"][f"message_{language.value}"]
                )
                if self.autonomy_mode != AutonomyMode.AUTONOMOUS:
                    self.create_checkpoint("user", checkpoint_msg)
                    await self.request_user_confirmation(checkpoint_msg)

            # Step 4: STRATEGIZE
            self.update_state("step", "STRATEGIZE")
            opponent_profile = await self.analyze_opponent(kwargs.get("opponent_info", {}))
            recommendation = await self.develop_strategy(
                analysis,
                risk_assessment,
                cost_estimate,
                opponent_profile,
                jurisdiction,
                language,
            )
            self._record_action(
                ActionType.GENERATE,
                "Strategy recommendation generated",
                inputs={"analysis_id": analysis.case_id},
                outputs={"strategy_type": recommendation.strategy_type.value},
                duration_ms=100,
            )

            # Check for aggressive strategy checkpoint
            if recommendation.strategy_type == StrategyType.AGGRESSIVE:
                checkpoint_msg = str(
                    STRATEGY_CHECKPOINTS["strategy_aggressive"][f"message_{language.value}"]
                )
                if self.autonomy_mode == AutonomyMode.CAUTIOUS:
                    self.create_checkpoint("user", checkpoint_msg)
                    await self.request_user_confirmation(checkpoint_msg)

            # Step 5: REVIEW and package deliverable
            self.update_state("step", "REVIEW")
            timeline = await self.generate_timeline(recommendation.strategy_type, jurisdiction)
            alternatives = self._generate_alternatives(
                analysis, risk_assessment, cost_estimate, jurisdiction, language
            )

            deliverable = StrategistDeliverable(
                recommendation=recommendation,
                case_analysis=analysis,
                alternative_strategies=alternatives,
                next_steps=recommendation.recommended_actions,
                warnings=self._generate_warnings(risk_assessment, cost_estimate, language),
                metadata={
                    "jurisdiction": jurisdiction.value,
                    "language": language.value,
                    "generated_at": datetime.utcnow().isoformat(),
                    "timeline": timeline,
                },
            )

            # Final checkpoint
            self.create_checkpoint("auto", "Strategy development completed")

            # Calculate execution time
            execution_time_ms = int((datetime.utcnow() - self._start_time).total_seconds() * 1000)

            return AgentResult(
                success=True,
                outcome=AgentOutcome.SUCCESS,
                deliverable=deliverable,
                partial_results=None,
                error_message=None,
                audit_log=self._create_audit_log(
                    AgentOutcome.SUCCESS,
                    ["strategy_recommendation", "case_analysis"],
                ),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._handle_error(e, recoverable=False)
            execution_time_ms = int((datetime.utcnow() - self._start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                outcome=AgentOutcome.FAILED,
                deliverable=None,
                partial_results=None,  # Type requires T | None, not dict
                error_message=str(e),
                audit_log=self._create_audit_log(AgentOutcome.FAILED, []),
                execution_time_ms=execution_time_ms,
            )

    # =========================================================================
    # HIGH PRIORITY METHODS
    # =========================================================================

    async def analyze_case(self, facts: CaseFacts) -> CaseAnalysis:
        """
        Analyze case facts and identify legal issues.

        Parses the case summary and structured facts to identify:
        - Core legal issues
        - Key facts supporting each party
        - Disputed vs undisputed matters
        - Evidence assessment
        - Preliminary legal position

        Args:
            facts: Structured case facts

        Returns:
            CaseAnalysis with comprehensive breakdown
        """
        logger.info("Analyzing case facts")

        # Extract legal issues from summary and questions
        legal_issues = list(facts.legal_questions) if facts.legal_questions else []

        # Add common Swiss law issues based on summary keywords
        summary_lower = facts.summary.lower()
        if "vertrag" in summary_lower or "contrat" in summary_lower or "contratto" in summary_lower:
            if "Art. 97 OR" not in " ".join(legal_issues) and "art. 97 CO" not in " ".join(
                legal_issues
            ):
                legal_issues.append("Vertragsverletzung (Art. 97 OR)")

        if "schaden" in summary_lower or "dommage" in summary_lower or "danno" in summary_lower:
            if "Schadenersatz" not in " ".join(legal_issues):
                legal_issues.append("Schadenersatzberechnung")

        # Extract key facts from events
        key_facts = (
            [event.get("event", str(event)) for event in facts.key_events[:5]]
            if facts.key_events
            else [facts.summary[:200]]
        )

        # Evidence assessment
        evidence_assessment = {}
        for evidence in facts.evidence_available:
            # Simple scoring based on evidence type
            if any(
                kw in evidence.lower() for kw in ["vertrag", "contrat", "contratto", "contract"]
            ):
                evidence_assessment[evidence] = "strong"
            elif any(kw in evidence.lower() for kw in ["gutachten", "expertise", "perizia"]):
                evidence_assessment[evidence] = "strong"
            elif any(kw in evidence.lower() for kw in ["email", "e-mail", "korrespondenz"]):
                evidence_assessment[evidence] = "moderate"
            else:
                evidence_assessment[evidence] = "supporting"

        # Calculate confidence based on evidence quality
        strong_count = sum(1 for v in evidence_assessment.values() if v == "strong")
        total_count = len(evidence_assessment) or 1
        confidence = min(0.9, 0.5 + (strong_count / total_count) * 0.4)

        return CaseAnalysis(
            case_id=str(uuid.uuid4())[:8],
            legal_issues=legal_issues,
            key_facts=key_facts,
            disputed_matters=facts.disputed_facts,
            evidence_assessment=evidence_assessment,
            jurisdictional_analysis={
                "federal_competence": any(
                    "bundesgericht" in i.lower() or "BGG" in i for i in legal_issues
                ),
                "cantonal_competence": True,
            },
            preliminary_position="favorable" if confidence > 0.65 else "uncertain",
            confidence_score=confidence,
        )

    async def assess_risk(
        self,
        analysis: CaseAnalysis,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
    ) -> RiskAssessment:
        """
        Comprehensive risk evaluation across multiple dimensions.

        Evaluates:
        - Litigation risk (procedural and substantive)
        - Cost risk (escalation potential)
        - Reputation risk

        Args:
            analysis: Case analysis results
            jurisdiction: Target jurisdiction

        Returns:
            RiskAssessment with weighted scoring
        """
        logger.info("Assessing litigation risks")

        # Calculate litigation risk based on disputed matters and evidence
        disputed_count = len(analysis.disputed_matters)
        evidence_strength = sum(1 for v in analysis.evidence_assessment.values() if v == "strong")

        if disputed_count <= 1 and evidence_strength >= 2:
            litigation_risk = RiskLevel.LOW
        elif disputed_count <= 2 and evidence_strength >= 1:
            litigation_risk = RiskLevel.MEDIUM
        elif disputed_count >= 3 or evidence_strength == 0:
            litigation_risk = RiskLevel.HIGH
        else:
            litigation_risk = RiskLevel.MEDIUM

        # Cost risk based on complexity and jurisdiction
        if len(analysis.legal_issues) >= 4 or jurisdiction == Jurisdiction.FEDERAL:
            cost_risk = RiskLevel.HIGH
        elif len(analysis.legal_issues) >= 2:
            cost_risk = RiskLevel.MEDIUM
        else:
            cost_risk = RiskLevel.LOW

        # Reputation risk (simplified assessment)
        reputation_risk = RiskLevel.LOW  # Default, would need more context

        # Calculate overall risk level
        risk_scores = [
            litigation_risk.numeric_score * 0.5,
            cost_risk.numeric_score * 0.3,
            reputation_risk.numeric_score * 0.2,
        ]
        avg_score = sum(risk_scores)

        if avg_score >= 0.7:
            overall_level = RiskLevel.HIGH
        elif avg_score >= 0.5:
            overall_level = RiskLevel.MEDIUM
        elif avg_score >= 0.3:
            overall_level = RiskLevel.LOW
        else:
            overall_level = RiskLevel.VERY_LOW

        # Generate risk factors and mitigations
        factors = []
        mitigations = []

        if disputed_count > 0:
            factors.append(f"{disputed_count} disputed fact(s) create uncertainty")
            mitigations.append("Strengthen evidence on disputed matters")

        if litigation_risk.numeric_score >= 0.5:
            factors.append("Substantive legal risk in key claims")
            mitigations.append("Consider settlement discussions early")

        if cost_risk.numeric_score >= 0.7:
            factors.append("Complex case may escalate costs")
            mitigations.append("Set clear budget limits with client")

        return RiskAssessment(
            overall_level=overall_level,
            litigation_risk=litigation_risk,
            cost_risk=cost_risk,
            reputation_risk=reputation_risk,
            factors=factors,
            mitigations=mitigations,
            confidence_score=analysis.confidence_score,
        )

    async def estimate_costs(
        self,
        strategy: StrategyType,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        value_in_dispute: float = 100000.0,
    ) -> CostEstimate:
        """
        Cost-benefit analysis with CHF estimates.

        Calculates:
        - Attorney fees based on complexity
        - Court costs by jurisdiction
        - Expert fees if applicable
        - Recovery potential

        Args:
            strategy: Selected strategy type
            jurisdiction: Target jurisdiction
            value_in_dispute: Streitwert/valeur litigieuse

        Returns:
            CostEstimate with detailed breakdown
        """
        logger.info(f"Estimating costs for {strategy.value} strategy")

        # Get court cost table
        cost_table = self.COURT_COST_TABLES.get(jurisdiction, self.COURT_COST_TABLES["default"])

        # Find applicable range
        court_min, court_max = 1000, 10000  # Default
        for (low, high), (cost_low, cost_high) in cost_table.items():
            if low <= value_in_dispute < high:
                court_min, court_max = cost_low, cost_high
                break

        # Calculate attorney fees based on strategy
        base_hours = {
            StrategyType.AGGRESSIVE: (80, 150),
            StrategyType.DEFENSIVE: (40, 80),
            StrategyType.SETTLEMENT: (20, 50),
            StrategyType.HYBRID: (60, 120),
        }
        min_hours, max_hours = base_hours[strategy]

        # Average rate between associate and senior associate
        avg_rate = (
            self.ATTORNEY_RATES["associate"][1] + self.ATTORNEY_RATES["senior_associate"][0]
        ) / 2

        attorney_min = min_hours * self.ATTORNEY_RATES["associate"][0]
        attorney_max = max_hours * self.ATTORNEY_RATES["senior_associate"][1]
        attorney_likely = int((min_hours + max_hours) / 2 * avg_rate)

        # Expert fees (estimated)
        expert_min = 2000 if strategy != StrategyType.SETTLEMENT else 0
        expert_max = 10000 if strategy == StrategyType.AGGRESSIVE else 5000

        # Calculate totals
        minimum_chf = attorney_min + court_min + expert_min
        maximum_chf = attorney_max + court_max + expert_max
        most_likely_chf = (
            attorney_likely + (court_min + court_max) / 2 + (expert_min + expert_max) / 2
        )

        # Recovery potential (simplified)
        recovery_potential = min(value_in_dispute * 0.1, 15000.0)  # Cost allocation

        return CostEstimate(
            minimum_chf=minimum_chf,
            maximum_chf=maximum_chf,
            most_likely_chf=most_likely_chf,
            breakdown={
                "attorney_fees": attorney_likely,
                "court_costs": (court_min + court_max) / 2,
                "expert_fees": (expert_min + expert_max) / 2,
            },
            assumptions=[
                f"Based on {strategy.value} litigation strategy",
                f"Streitwert: CHF {value_in_dispute:,.0f}",
                "Standard proceedings without appeals",
            ],
            court_costs=(court_min + court_max) / 2,
            expert_fees=(expert_min + expert_max) / 2,
            recovery_potential=recovery_potential,
        )

    async def develop_strategy(
        self,
        analysis: CaseAnalysis,
        risk: RiskAssessment,
        cost: CostEstimate,
        opponent: OpponentProfile | None,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        language: Language = Language.DE,
    ) -> StrategyRecommendation:
        """
        Develop and recommend litigation strategy.

        Synthesizes analysis, risk, cost, and opponent profile to
        generate comprehensive strategy recommendation.

        Args:
            analysis: Case analysis results
            risk: Risk assessment
            cost: Cost estimate
            opponent: Optional opponent profile
            jurisdiction: Target jurisdiction
            language: Output language

        Returns:
            StrategyRecommendation with full details
        """
        logger.info("Developing strategy recommendation")

        # Determine optimal strategy type
        strategy_type = self._determine_optimal_strategy(analysis, risk, cost, opponent)

        # Calculate success probability
        success_prob = self._calculate_success_probability(
            analysis.confidence_score, risk.overall_level, strategy_type
        )

        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(strategy_type, analysis, language)

        # Identify key arguments and weak points
        legal_basis = analysis.legal_issues[0] if analysis.legal_issues else "to be determined"
        key_arguments = [
            f"Clear legal basis for claim ({legal_basis})",
            "Documented evidence chain available",
        ]
        if analysis.preliminary_position == "favorable":
            key_arguments.append("Favorable preliminary assessment of merits")

        weak_points = analysis.disputed_matters[:3] if analysis.disputed_matters else []

        # Generate timeline
        timeline_weeks = {
            StrategyType.AGGRESSIVE: 36,
            StrategyType.DEFENSIVE: 24,
            StrategyType.SETTLEMENT: 12,
            StrategyType.HYBRID: 24,
        }[strategy_type]

        # Alternative strategies
        alternatives = self._generate_strategy_alternatives(analysis, risk, language)

        return StrategyRecommendation(
            strategy_type=strategy_type,
            success_probability=success_prob,
            risk_assessment=risk,
            cost_estimate=cost,
            recommended_actions=recommended_actions,
            alternative_strategies=alternatives,
            key_arguments=key_arguments,
            weak_points=weak_points,
            timeline_weeks=timeline_weeks,
            checkpoints=[
                "Initial pleadings filed",
                "Evidence exchange complete",
                "Settlement discussions",
                "Trial preparation",
            ],
            opponent_profile=opponent,
            jurisdiction=jurisdiction,
            language=language,
            confidence_score=analysis.confidence_score,
        )

    # =========================================================================
    # MEDIUM PRIORITY METHODS
    # =========================================================================

    async def analyze_opponent(self, opponent_info: dict[str, Any]) -> OpponentProfile | None:
        """
        Analyze opposing party's likely strategy and profile.

        Args:
            opponent_info: Available information about opponent

        Returns:
            OpponentProfile if sufficient information available
        """
        if not opponent_info:
            return None

        name = opponent_info.get("name", "Unknown")
        logger.info(f"Analyzing opponent: {name}")

        return OpponentProfile(
            name=name,
            legal_representation=opponent_info.get("representation", "Unknown"),
            litigation_history=opponent_info.get("history", []),
            financial_capacity=opponent_info.get("financial_capacity", "unknown"),
            settlement_tendency=opponent_info.get("settlement_tendency", "unknown"),
            strengths=opponent_info.get("strengths", []),
            weaknesses=opponent_info.get("weaknesses", []),
            notes=opponent_info.get("notes", ""),
        )

    async def generate_timeline(
        self,
        strategy: StrategyType,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
    ) -> list[dict[str, Any]]:
        """
        Generate procedural timeline with milestones.

        Args:
            strategy: Selected strategy
            jurisdiction: Target jurisdiction

        Returns:
            List of timeline milestones
        """
        logger.info(f"Generating timeline for {strategy.value} strategy")

        base_timeline = [
            {"week": 0, "milestone": "Klageeinreichung", "critical": True},
            {"week": 4, "milestone": "Klageantwort erwartet", "critical": True},
            {"week": 8, "milestone": "Replik/Duplik", "critical": False},
            {"week": 12, "milestone": "Beweisverfahren", "critical": True},
            {"week": 20, "milestone": "Hauptverhandlung", "critical": True},
            {"week": 24, "milestone": "Urteil", "critical": True},
        ]

        # Adjust for strategy type
        if strategy == StrategyType.SETTLEMENT:
            base_timeline = [
                {"week": 0, "milestone": "Vergleichsgespräche initiieren", "critical": True},
                {"week": 4, "milestone": "Vergleichsangebot", "critical": True},
                {"week": 8, "milestone": "Verhandlungen", "critical": False},
                {"week": 12, "milestone": "Abschluss angestrebt", "critical": True},
            ]
        elif strategy == StrategyType.AGGRESSIVE:
            # Add interim measures
            base_timeline.insert(
                1, {"week": 1, "milestone": "Vorsorgliche Massnahmen prüfen", "critical": False}
            )

        return base_timeline

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _determine_initial_strategy(
        self, analysis: CaseAnalysis, risk: RiskAssessment
    ) -> StrategyType:
        """Determine initial strategy based on analysis and risk."""
        if risk.overall_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            return StrategyType.SETTLEMENT
        elif analysis.preliminary_position == "favorable" and risk.overall_level == RiskLevel.LOW:
            return StrategyType.AGGRESSIVE
        else:
            return StrategyType.HYBRID

    def _determine_optimal_strategy(
        self,
        analysis: CaseAnalysis,
        risk: RiskAssessment,
        cost: CostEstimate,
        opponent: OpponentProfile | None,
    ) -> StrategyType:
        """Determine optimal strategy considering all factors."""
        # Start with initial determination
        initial = self._determine_initial_strategy(analysis, risk)

        # Adjust based on cost-benefit
        if cost.net_cost_if_successful < 0:  # Net cost even if successful
            return StrategyType.SETTLEMENT

        # Adjust based on opponent profile
        if opponent and opponent.settlement_tendency == "likely":
            if initial == StrategyType.AGGRESSIVE:
                return StrategyType.HYBRID  # Moderate to encourage settlement

        return initial

    def _calculate_success_probability(
        self,
        confidence: float,
        risk_level: RiskLevel,
        strategy: StrategyType,
    ) -> SuccessProbability:
        """Calculate success probability based on factors."""
        # Base probability from confidence
        base_prob = confidence

        # Adjust for risk level
        risk_adjustments = {
            RiskLevel.VERY_LOW: 0.1,
            RiskLevel.LOW: 0.05,
            RiskLevel.MEDIUM: 0,
            RiskLevel.HIGH: -0.1,
            RiskLevel.VERY_HIGH: -0.2,
        }
        adjusted = base_prob + risk_adjustments.get(risk_level, 0)

        # Strategy adjustments
        if strategy == StrategyType.SETTLEMENT:
            adjusted += 0.1  # Higher success in achieving settlement

        return SuccessProbability.from_percentage(adjusted)

    def _generate_recommended_actions(
        self,
        strategy: StrategyType,
        analysis: CaseAnalysis,
        language: Language,
    ) -> list[str]:
        """Generate recommended actions based on strategy."""
        actions_by_strategy = {
            StrategyType.AGGRESSIVE: {
                Language.DE: [
                    "Klage innerhalb von 30 Tagen einreichen",
                    "Vorsorgliche Massnahmen prüfen",
                    "Umfassende Beweisdokumentation vorbereiten",
                    "Pressemitteilung erwägen (falls angemessen)",
                ],
                Language.FR: [
                    "Déposer la demande dans les 30 jours",
                    "Examiner les mesures provisionnelles",
                    "Préparer documentation complète des preuves",
                    "Considérer communiqué de presse (si approprié)",
                ],
                Language.IT: [
                    "Presentare la petizione entro 30 giorni",
                    "Esaminare misure cautelari",
                    "Preparare documentazione completa delle prove",
                    "Considerare comunicato stampa (se appropriato)",
                ],
                Language.EN: [
                    "File claim within 30 days",
                    "Evaluate interim measures",
                    "Prepare comprehensive evidence documentation",
                    "Consider press release (if appropriate)",
                ],
            },
            StrategyType.SETTLEMENT: {
                Language.DE: [
                    "Vergleichsgespräche initiieren",
                    "Vergleichsangebot vorbereiten",
                    "Mediator identifizieren",
                ],
                Language.FR: [
                    "Initier les discussions de règlement",
                    "Préparer offre de règlement",
                    "Identifier médiateur",
                ],
                Language.IT: [
                    "Avviare discussioni di transazione",
                    "Preparare offerta di transazione",
                    "Identificare mediatore",
                ],
                Language.EN: [
                    "Initiate settlement discussions",
                    "Prepare settlement offer",
                    "Identify mediator",
                ],
            },
        }

        # Default hybrid actions
        default_actions = {
            Language.DE: [
                "Klage vorbereiten, parallel Vergleich suchen",
                "Beweisdokumentation erstellen",
                "Kostenbudget mit Mandant besprechen",
            ],
            Language.FR: [
                "Préparer demande, rechercher règlement en parallèle",
                "Créer documentation des preuves",
                "Discuter budget avec client",
            ],
            Language.IT: [
                "Preparare petizione, cercare transazione in parallelo",
                "Creare documentazione delle prove",
                "Discutere budget con cliente",
            ],
            Language.EN: [
                "Prepare claim while pursuing settlement",
                "Create evidence documentation",
                "Discuss budget with client",
            ],
        }

        strategy_actions = actions_by_strategy.get(strategy, {})
        return strategy_actions.get(language, default_actions.get(language, []))

    def _generate_alternatives(
        self,
        analysis: CaseAnalysis,
        risk: RiskAssessment,
        cost: CostEstimate,
        jurisdiction: Jurisdiction,
        language: Language,
    ) -> list[dict[str, Any]]:
        """Generate alternative strategy options."""
        return [
            {
                "type": "settlement",
                "description_de": "Direkter Vergleich ohne Gerichtsverfahren",
                "description_fr": "Règlement direct sans procédure judiciaire",
                "description_it": "Transazione diretta senza procedura giudiziaria",
                "pros": ["Lower costs", "Quick resolution", "Confidential"],
                "cons": ["Potentially lower recovery", "May show weakness"],
            },
            {
                "type": "mediation",
                "description_de": "Mediation vor Klageeinreichung",
                "description_fr": "Médiation avant dépôt de demande",
                "description_it": "Mediazione prima della petizione",
                "pros": ["Preserves relationship", "Cost-effective"],
                "cons": ["Not binding", "Time investment"],
            },
        ]

    def _generate_strategy_alternatives(
        self,
        analysis: CaseAnalysis,
        risk: RiskAssessment,
        language: Language,
    ) -> list[dict[str, Any]]:
        """Generate alternative strategy summaries for recommendation."""
        return [
            {
                "type": "aggressive",
                "description": "Full litigation without settlement attempts",
                "pros": ["Potentially higher recovery"],
                "cons": ["Higher costs", "Longer timeline"],
            },
            {
                "type": "settlement",
                "description": "Direct settlement negotiation",
                "pros": ["Quick resolution", "Lower costs"],
                "cons": ["Potentially lower recovery"],
            },
        ]

    def _generate_warnings(
        self,
        risk: RiskAssessment,
        cost: CostEstimate,
        language: Language,
    ) -> list[str]:
        """Generate warnings based on risk and cost analysis."""
        warnings = []

        if risk.overall_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            warning_msgs = {
                Language.DE: "⚠️ Hohe Risikowarnung: Sorgfältige Überprüfung empfohlen",
                Language.FR: "⚠️ Avertissement risque élevé: Examen attentif recommandé",
                Language.IT: "⚠️ Avviso rischio elevato: Esame attento raccomandato",
                Language.EN: "⚠️ High risk warning: Careful review recommended",
            }
            warnings.append(warning_msgs.get(language, warning_msgs[Language.EN]))

        if cost.maximum_chf > 100000:
            warning_msgs = {
                Language.DE: "💰 Hohe potenzielle Kosten: Budgetplanung erforderlich",
                Language.FR: "💰 Coûts potentiels élevés: Planification budgétaire requise",
                Language.IT: "💰 Costi potenziali elevati: Pianificazione del budget richiesta",
                Language.EN: "💰 High potential costs: Budget planning required",
            }
            warnings.append(warning_msgs.get(language, warning_msgs[Language.EN]))

        return warnings
