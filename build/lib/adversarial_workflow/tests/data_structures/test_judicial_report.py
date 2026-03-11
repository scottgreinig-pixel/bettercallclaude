"""
Tests for JudicialReport data structure.

This module contains comprehensive tests for the JudicialReport schema
used in the adversarial workflow system for Swiss legal analysis.

Test Coverage:
- Synthesis validation (balanced analysis, convergent/divergent points)
- RiskAssessment validation (probabilities sum to 1.0, confidence range)
- LegalConclusion validation (primary outcome, alternatives)
- JudicialReport structure validation
- YAML serialization/deserialization
- Probability validation (sum ±0.05 tolerance)
- Confidence level constraints (0.0-1.0)
"""

import pytest

from adversarial_workflow.data_structures.judicial_report import (
    JudicialReport,
    LegalConclusion,
    RiskAssessment,
    Synthesis,
)


class TestSynthesis:
    """Test cases for Synthesis dataclass."""

    def test_valid_synthesis_creation(self) -> None:
        """Test creating a valid synthesis."""
        synthesis = Synthesis(
            balanced_analysis="Objective analysis balancing both positions.",
            convergent_points=["Both agree on statutory interpretation"],
            divergent_points=["Disagree on factual causation"],
        )
        assert synthesis.balanced_analysis == "Objective analysis balancing both positions."
        assert len(synthesis.convergent_points) == 1
        assert len(synthesis.divergent_points) == 1

    def test_balanced_analysis_required(self) -> None:
        """Test that balanced_analysis cannot be empty."""
        with pytest.raises(ValueError, match="balanced_analysis cannot be empty"):
            Synthesis(
                balanced_analysis="",
                convergent_points=["Point"],
                divergent_points=[],
            )

    def test_balanced_analysis_minimum_length(self) -> None:
        """Test that balanced_analysis has minimum 20 characters."""
        with pytest.raises(ValueError, match="balanced_analysis must be at least 20 characters"):
            Synthesis(
                balanced_analysis="Too short",
                convergent_points=[],
                divergent_points=[],
            )

    def test_empty_convergent_points_allowed(self) -> None:
        """Test that convergent_points can be empty list."""
        synthesis = Synthesis(
            balanced_analysis="Analysis with no convergence found in positions.",
            convergent_points=[],
            divergent_points=["Complete disagreement on liability"],
        )
        assert synthesis.convergent_points == []

    def test_empty_divergent_points_allowed(self) -> None:
        """Test that divergent_points can be empty list."""
        synthesis = Synthesis(
            balanced_analysis="Analysis with complete agreement on all points.",
            convergent_points=["Full agreement on all elements"],
            divergent_points=[],
        )
        assert synthesis.divergent_points == []


class TestRiskAssessment:
    """Test cases for RiskAssessment dataclass."""

    def test_valid_risk_assessment_creation(self) -> None:
        """Test creating a valid risk assessment."""
        risk = RiskAssessment(
            favorable_probability=0.65,
            unfavorable_probability=0.35,
            confidence_level=0.80,
        )
        assert risk.favorable_probability == 0.65
        assert risk.unfavorable_probability == 0.35
        assert risk.confidence_level == 0.80

    def test_probabilities_sum_to_one(self) -> None:
        """Test that probabilities must sum to 1.0 within tolerance."""
        # Exact sum
        risk = RiskAssessment(
            favorable_probability=0.60,
            unfavorable_probability=0.40,
            confidence_level=0.75,
        )
        assert abs(risk.favorable_probability + risk.unfavorable_probability - 1.0) < 0.001

    def test_probabilities_sum_within_tolerance(self) -> None:
        """Test that probabilities within ±0.05 tolerance are accepted."""
        # Within tolerance (+0.04)
        risk = RiskAssessment(
            favorable_probability=0.54,
            unfavorable_probability=0.50,
            confidence_level=0.70,
        )
        assert risk.favorable_probability == 0.54
        assert risk.unfavorable_probability == 0.50

    def test_probabilities_sum_below_tolerance(self) -> None:
        """Test that probabilities sum too low is rejected."""
        with pytest.raises(
            ValueError, match="favorable_probability and unfavorable_probability must sum to 1.0"
        ):
            RiskAssessment(
                favorable_probability=0.40,
                unfavorable_probability=0.40,  # Sum = 0.80 (too low)
                confidence_level=0.75,
            )

    def test_probabilities_sum_above_tolerance(self) -> None:
        """Test that probabilities sum too high is rejected."""
        with pytest.raises(
            ValueError, match="favorable_probability and unfavorable_probability must sum to 1.0"
        ):
            RiskAssessment(
                favorable_probability=0.60,
                unfavorable_probability=0.60,  # Sum = 1.20 (too high)
                confidence_level=0.75,
            )

    def test_favorable_probability_negative(self) -> None:
        """Test that negative favorable_probability is rejected."""
        with pytest.raises(ValueError, match="favorable_probability must be between 0.0 and 1.0"):
            RiskAssessment(
                favorable_probability=-0.1,
                unfavorable_probability=1.1,
                confidence_level=0.75,
            )

    def test_favorable_probability_above_one(self) -> None:
        """Test that favorable_probability > 1.0 is rejected."""
        with pytest.raises(ValueError, match="favorable_probability must be between 0.0 and 1.0"):
            RiskAssessment(
                favorable_probability=1.5,
                unfavorable_probability=-0.5,
                confidence_level=0.75,
            )

    def test_unfavorable_probability_negative(self) -> None:
        """Test that negative unfavorable_probability is rejected."""
        with pytest.raises(ValueError, match="unfavorable_probability must be between 0.0 and 1.0"):
            RiskAssessment(
                favorable_probability=0.6,
                unfavorable_probability=-0.1,
                confidence_level=0.75,
            )

    def test_unfavorable_probability_above_one(self) -> None:
        """Test that unfavorable_probability > 1.0 is rejected."""
        with pytest.raises(ValueError, match="unfavorable_probability must be between 0.0 and 1.0"):
            RiskAssessment(
                favorable_probability=0.5,
                unfavorable_probability=1.5,
                confidence_level=0.75,
            )

    def test_confidence_level_minimum(self) -> None:
        """Test that confidence_level cannot be negative."""
        with pytest.raises(ValueError, match="confidence_level must be between 0.0 and 1.0"):
            RiskAssessment(
                favorable_probability=0.60,
                unfavorable_probability=0.40,
                confidence_level=-0.1,
            )

    def test_confidence_level_maximum(self) -> None:
        """Test that confidence_level cannot exceed 1.0."""
        with pytest.raises(ValueError, match="confidence_level must be between 0.0 and 1.0"):
            RiskAssessment(
                favorable_probability=0.60,
                unfavorable_probability=0.40,
                confidence_level=1.5,
            )

    def test_confidence_level_boundary_values(self) -> None:
        """Test confidence_level at boundary values 0.0 and 1.0."""
        # Test minimum boundary
        risk_min = RiskAssessment(
            favorable_probability=0.50,
            unfavorable_probability=0.50,
            confidence_level=0.0,
        )
        assert risk_min.confidence_level == 0.0

        # Test maximum boundary
        risk_max = RiskAssessment(
            favorable_probability=0.50,
            unfavorable_probability=0.50,
            confidence_level=1.0,
        )
        assert risk_max.confidence_level == 1.0


class TestLegalConclusion:
    """Test cases for LegalConclusion dataclass."""

    def test_valid_legal_conclusion_creation(self) -> None:
        """Test creating a valid legal conclusion."""
        conclusion = LegalConclusion(
            primary_outcome="Claim likely to succeed based on preponderance of evidence.",
            alternative_outcomes=[
                "Partial success if damages reduced",
                "Settlement recommended given litigation risks",
            ],
        )
        assert (
            conclusion.primary_outcome
            == "Claim likely to succeed based on preponderance of evidence."
        )
        assert len(conclusion.alternative_outcomes) == 2

    def test_primary_outcome_required(self) -> None:
        """Test that primary_outcome cannot be empty."""
        with pytest.raises(ValueError, match="primary_outcome cannot be empty"):
            LegalConclusion(
                primary_outcome="",
                alternative_outcomes=["Alternative"],
            )

    def test_primary_outcome_minimum_length(self) -> None:
        """Test that primary_outcome has minimum 20 characters."""
        with pytest.raises(ValueError, match="primary_outcome must be at least 20 characters"):
            LegalConclusion(
                primary_outcome="Too short",
                alternative_outcomes=[],
            )

    def test_empty_alternative_outcomes_allowed(self) -> None:
        """Test that alternative_outcomes can be empty list."""
        conclusion = LegalConclusion(
            primary_outcome="Clear outcome with no reasonable alternatives.",
            alternative_outcomes=[],
        )
        assert conclusion.alternative_outcomes == []


class TestJudicialReport:
    """Test cases for JudicialReport dataclass."""

    def test_valid_judicial_report_creation(self) -> None:
        """Test creating a valid judicial report."""
        report = JudicialReport(
            synthesis=Synthesis(
                balanced_analysis="Objective synthesis balancing advocate and adversary positions.",
                convergent_points=["Both agree on statutory basis"],
                divergent_points=["Disagree on factual causation"],
            ),
            risk_assessment=RiskAssessment(
                favorable_probability=0.65,
                unfavorable_probability=0.35,
                confidence_level=0.80,
            ),
            legal_conclusion=LegalConclusion(
                primary_outcome="Claim likely to succeed on balance of probabilities.",
                alternative_outcomes=["Partial success possible", "Settlement recommended"],
            ),
        )
        assert report.synthesis.balanced_analysis.startswith("Objective synthesis")
        assert report.risk_assessment.favorable_probability == 0.65
        assert report.legal_conclusion.primary_outcome.startswith("Claim likely")

    def test_synthesis_required(self) -> None:
        """Test that synthesis component is required."""
        # This test ensures synthesis parameter is not optional
        # Python will raise TypeError if missing, not ValueError
        with pytest.raises(TypeError):
            JudicialReport(
                risk_assessment=RiskAssessment(
                    favorable_probability=0.60,
                    unfavorable_probability=0.40,
                    confidence_level=0.75,
                ),
                legal_conclusion=LegalConclusion(
                    primary_outcome="Outcome text here for validation.",
                    alternative_outcomes=[],
                ),
            )

    def test_risk_assessment_required(self) -> None:
        """Test that risk_assessment component is required."""
        with pytest.raises(TypeError):
            JudicialReport(
                synthesis=Synthesis(
                    balanced_analysis="Analysis text here for validation purposes.",
                    convergent_points=[],
                    divergent_points=[],
                ),
                legal_conclusion=LegalConclusion(
                    primary_outcome="Outcome text here for validation.",
                    alternative_outcomes=[],
                ),
            )

    def test_legal_conclusion_required(self) -> None:
        """Test that legal_conclusion component is required."""
        with pytest.raises(TypeError):
            JudicialReport(
                synthesis=Synthesis(
                    balanced_analysis="Analysis text here for validation purposes.",
                    convergent_points=[],
                    divergent_points=[],
                ),
                risk_assessment=RiskAssessment(
                    favorable_probability=0.60,
                    unfavorable_probability=0.40,
                    confidence_level=0.75,
                ),
            )


class TestJudicialReportSerialization:
    """Test YAML serialization/deserialization for JudicialReport."""

    def test_to_dict(self) -> None:
        """Test converting JudicialReport to dictionary."""
        report = JudicialReport(
            synthesis=Synthesis(
                balanced_analysis="Balanced analysis of pro and anti positions presented.",
                convergent_points=["Statutory interpretation agreed"],
                divergent_points=["Factual causation disputed"],
            ),
            risk_assessment=RiskAssessment(
                favorable_probability=0.65,
                unfavorable_probability=0.35,
                confidence_level=0.80,
            ),
            legal_conclusion=LegalConclusion(
                primary_outcome="Success likely based on legal analysis presented.",
                alternative_outcomes=["Partial success", "Settlement"],
            ),
        )

        result = report.to_dict()
        assert result["synthesis"]["balanced_analysis"].startswith("Balanced analysis")
        assert result["risk_assessment"]["favorable_probability"] == 0.65
        assert result["legal_conclusion"]["primary_outcome"].startswith("Success likely")

    def test_from_dict(self) -> None:
        """Test creating JudicialReport from dictionary."""
        data = {
            "synthesis": {
                "balanced_analysis": "Objective analysis balancing both positions effectively.",
                "convergent_points": ["Agreement on legal framework"],
                "divergent_points": ["Disagreement on application"],
            },
            "risk_assessment": {
                "favorable_probability": 0.70,
                "unfavorable_probability": 0.30,
                "confidence_level": 0.85,
            },
            "legal_conclusion": {
                "primary_outcome": "Strong case for success on merits of claim.",
                "alternative_outcomes": ["Negotiated settlement"],
            },
        }

        report = JudicialReport.from_dict(data)
        assert (
            report.synthesis.balanced_analysis
            == "Objective analysis balancing both positions effectively."
        )
        assert report.risk_assessment.favorable_probability == 0.70
        assert (
            report.legal_conclusion.primary_outcome == "Strong case for success on merits of claim."
        )

    def test_to_yaml(self) -> None:
        """Test converting JudicialReport to YAML string."""
        report = JudicialReport(
            synthesis=Synthesis(
                balanced_analysis="Analysis balancing advocate and adversary positions.",
                convergent_points=["Common ground identified"],
                divergent_points=[],
            ),
            risk_assessment=RiskAssessment(
                favorable_probability=0.60,
                unfavorable_probability=0.40,
                confidence_level=0.75,
            ),
            legal_conclusion=LegalConclusion(
                primary_outcome="Moderate likelihood of success in litigation.",
                alternative_outcomes=[],
            ),
        )

        yaml_str = report.to_yaml()
        assert isinstance(yaml_str, str)
        assert "balanced_analysis:" in yaml_str
        assert "favorable_probability: 0.6" in yaml_str
        assert "primary_outcome:" in yaml_str

    def test_from_yaml(self) -> None:
        """Test creating JudicialReport from YAML string."""
        yaml_str = """
synthesis:
  balanced_analysis: Comprehensive analysis balancing all positions.
  convergent_points:
    - Both parties agree on statutory interpretation
  divergent_points:
    - Factual causation remains disputed
risk_assessment:
  favorable_probability: 0.65
  unfavorable_probability: 0.35
  confidence_level: 0.80
legal_conclusion:
  primary_outcome: Success probable based on balanced analysis.
  alternative_outcomes:
    - Partial success on damages
    - Settlement before trial
"""

        report = JudicialReport.from_yaml(yaml_str)
        assert (
            report.synthesis.balanced_analysis == "Comprehensive analysis balancing all positions."
        )
        assert len(report.synthesis.convergent_points) == 1
        assert report.risk_assessment.favorable_probability == 0.65
        assert (
            report.legal_conclusion.primary_outcome
            == "Success probable based on balanced analysis."
        )

    def test_round_trip_serialization(self) -> None:
        """Test round-trip YAML serialization maintains data integrity."""
        original = JudicialReport(
            synthesis=Synthesis(
                balanced_analysis="Detailed synthesis of advocate and adversary positions.",
                convergent_points=[
                    "Agreement on legal framework applicability",
                    "Common understanding of statutory requirements",
                ],
                divergent_points=[
                    "Interpretation of factual causation",
                    "Assessment of damages quantum",
                ],
            ),
            risk_assessment=RiskAssessment(
                favorable_probability=0.68,
                unfavorable_probability=0.32,
                confidence_level=0.82,
            ),
            legal_conclusion=LegalConclusion(
                primary_outcome="Claim success likely on balance of probabilities presented.",
                alternative_outcomes=[
                    "Partial success if damages reduced by court",
                    "Settlement recommended given litigation uncertainties",
                ],
            ),
        )

        # Convert to YAML and back
        yaml_str = original.to_yaml()
        restored = JudicialReport.from_yaml(yaml_str)

        # Verify all data preserved
        assert restored.synthesis.balanced_analysis == original.synthesis.balanced_analysis
        assert len(restored.synthesis.convergent_points) == len(
            original.synthesis.convergent_points
        )
        assert len(restored.synthesis.divergent_points) == len(original.synthesis.divergent_points)
        assert (
            restored.risk_assessment.favorable_probability
            == original.risk_assessment.favorable_probability
        )
        assert (
            restored.risk_assessment.unfavorable_probability
            == original.risk_assessment.unfavorable_probability
        )
        assert (
            restored.risk_assessment.confidence_level == original.risk_assessment.confidence_level
        )
        assert (
            restored.legal_conclusion.primary_outcome == original.legal_conclusion.primary_outcome
        )
        assert len(restored.legal_conclusion.alternative_outcomes) == len(
            original.legal_conclusion.alternative_outcomes
        )
