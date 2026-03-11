"""
Tests for AdvocateReport data structure.

This module contains comprehensive tests for the AdvocateReport schema
used in the adversarial workflow system for Swiss legal analysis.

Test Coverage:
- AdvocateReport validation
- Argument structure validation
- Citation validation
- YAML serialization/deserialization
- Position value constraints
- Strength value ranges
"""

import pytest

from adversarial_workflow.data_structures.advocate_report import (
    AdvocateReport,
    Argument,
    Citation,
)


class TestArgument:
    """Test cases for Argument dataclass."""

    def test_valid_argument_creation(self) -> None:
        """Test creating a valid argument."""
        arg = Argument(
            argument_id="ARG_001",
            statutory_basis=["Art. 97 OR"],
            precedents=["BGE 145 III 229"],
            reasoning="Contractual liability is established under Swiss law.",
            strength=0.85,
        )
        assert arg.argument_id == "ARG_001"
        assert arg.statutory_basis == ["Art. 97 OR"]
        assert arg.precedents == ["BGE 145 III 229"]
        assert arg.strength == 0.85

    def test_argument_id_required(self) -> None:
        """Test that argument_id cannot be empty."""
        with pytest.raises(ValueError, match="argument_id cannot be empty"):
            Argument(
                argument_id="",
                statutory_basis=["Art. 97 OR"],
                precedents=[],
                reasoning="Test reasoning text here.",
                strength=0.5,
            )

    def test_argument_id_whitespace_only(self) -> None:
        """Test that argument_id cannot be whitespace only."""
        with pytest.raises(ValueError, match="argument_id cannot be whitespace only"):
            Argument(
                argument_id="   ",
                statutory_basis=["Art. 97 OR"],
                precedents=[],
                reasoning="Test reasoning text here.",
                strength=0.5,
            )

    def test_reasoning_required(self) -> None:
        """Test that reasoning cannot be empty."""
        with pytest.raises(ValueError, match="reasoning cannot be empty"):
            Argument(
                argument_id="ARG_001",
                statutory_basis=["Art. 97 OR"],
                precedents=[],
                reasoning="",
                strength=0.5,
            )

    def test_reasoning_minimum_length(self) -> None:
        """Test that reasoning has minimum 20 characters."""
        with pytest.raises(ValueError, match="reasoning must be at least 20 characters"):
            Argument(
                argument_id="ARG_001",
                statutory_basis=[],
                precedents=[],
                reasoning="Too short",
                strength=0.5,
            )

    def test_strength_minimum_value(self) -> None:
        """Test that strength cannot be negative."""
        with pytest.raises(ValueError, match="strength must be between 0.0 and 1.0"):
            Argument(
                argument_id="ARG_001",
                statutory_basis=[],
                precedents=[],
                reasoning="Valid reasoning text here for testing purposes.",
                strength=-0.1,
            )

    def test_strength_maximum_value(self) -> None:
        """Test that strength cannot exceed 1.0."""
        with pytest.raises(ValueError, match="strength must be between 0.0 and 1.0"):
            Argument(
                argument_id="ARG_001",
                statutory_basis=[],
                precedents=[],
                reasoning="Valid reasoning text here for testing purposes.",
                strength=1.5,
            )

    def test_strength_boundary_values(self) -> None:
        """Test strength at boundary values 0.0 and 1.0."""
        # Test minimum boundary
        arg_min = Argument(
            argument_id="ARG_MIN",
            statutory_basis=[],
            precedents=[],
            reasoning="Minimum strength argument for boundary testing.",
            strength=0.0,
        )
        assert arg_min.strength == 0.0

        # Test maximum boundary
        arg_max = Argument(
            argument_id="ARG_MAX",
            statutory_basis=[],
            precedents=[],
            reasoning="Maximum strength argument for boundary testing.",
            strength=1.0,
        )
        assert arg_max.strength == 1.0


class TestCitation:
    """Test cases for Citation dataclass."""

    def test_valid_citation_creation(self) -> None:
        """Test creating a valid citation."""
        citation = Citation(
            citation_id="CIT_001",
            type="bge",
            reference="BGE 145 III 229 E. 4.2",
            verified=True,
        )
        assert citation.citation_id == "CIT_001"
        assert citation.type == "bge"
        assert citation.reference == "BGE 145 III 229 E. 4.2"
        assert citation.verified is True

    def test_citation_id_required(self) -> None:
        """Test that citation_id cannot be empty."""
        with pytest.raises(ValueError, match="citation_id cannot be empty"):
            Citation(
                citation_id="",
                type="statute",
                reference="Art. 97 OR",
                verified=True,
            )

    def test_citation_type_validation(self) -> None:
        """Test that citation type must be valid."""
        # Valid types should work
        for valid_type in ["bge", "statute", "doctrine"]:
            citation = Citation(
                citation_id=f"CIT_{valid_type}",
                type=valid_type,
                reference="Test reference",
                verified=False,
            )
            assert citation.type == valid_type

    def test_reference_required(self) -> None:
        """Test that reference cannot be empty."""
        with pytest.raises(ValueError, match="reference cannot be empty"):
            Citation(
                citation_id="CIT_001",
                type="bge",
                reference="",
                verified=True,
            )


class TestAdvocateReport:
    """Test cases for AdvocateReport dataclass."""

    def test_valid_advocate_report_creation(self) -> None:
        """Test creating a valid advocate report."""
        report = AdvocateReport(
            position="pro",
            arguments=[
                Argument(
                    argument_id="ARG_001",
                    statutory_basis=["Art. 97 OR"],
                    precedents=["BGE 145 III 229"],
                    reasoning="Liability is clearly established under contract law.",
                    strength=0.85,
                )
            ],
            citations=[
                Citation(
                    citation_id="CIT_001",
                    type="bge",
                    reference="BGE 145 III 229 E. 4.2",
                    verified=True,
                )
            ],
        )
        assert report.position == "pro"
        assert len(report.arguments) == 1
        assert len(report.citations) == 1

    def test_position_validation(self) -> None:
        """Test that position must be 'pro' or 'anti'."""
        # Valid positions should work
        for valid_pos in ["pro", "anti"]:
            report = AdvocateReport(
                position=valid_pos,
                arguments=[
                    Argument(
                        argument_id="ARG_TEST",
                        statutory_basis=[],
                        precedents=[],
                        reasoning="Valid argument text for position testing.",
                        strength=0.5,
                    )
                ],
                citations=[],
            )
            assert report.position == valid_pos

    def test_arguments_required(self) -> None:
        """Test that at least one argument is required."""
        with pytest.raises(ValueError, match="At least one argument is required"):
            AdvocateReport(
                position="pro",
                arguments=[],
                citations=[],
            )

    def test_multiple_arguments(self) -> None:
        """Test report with multiple arguments."""
        report = AdvocateReport(
            position="pro",
            arguments=[
                Argument(
                    argument_id="ARG_001",
                    statutory_basis=["Art. 97 OR"],
                    precedents=[],
                    reasoning="First argument supporting the position clearly.",
                    strength=0.7,
                ),
                Argument(
                    argument_id="ARG_002",
                    statutory_basis=["Art. 41 OR"],
                    precedents=["BGE 145 III 229"],
                    reasoning="Second argument provides additional support.",
                    strength=0.8,
                ),
            ],
            citations=[],
        )
        assert len(report.arguments) == 2
        assert report.arguments[0].argument_id == "ARG_001"
        assert report.arguments[1].argument_id == "ARG_002"


class TestAdvocateReportSerialization:
    """Test YAML serialization/deserialization for AdvocateReport."""

    def test_to_dict(self) -> None:
        """Test converting AdvocateReport to dictionary."""
        report = AdvocateReport(
            position="pro",
            arguments=[
                Argument(
                    argument_id="ARG_001",
                    statutory_basis=["Art. 97 OR"],
                    precedents=["BGE 145 III 229"],
                    reasoning="Contractual liability established under Swiss law.",
                    strength=0.85,
                )
            ],
            citations=[
                Citation(
                    citation_id="CIT_001",
                    type="bge",
                    reference="BGE 145 III 229 E. 4.2",
                    verified=True,
                )
            ],
        )

        result = report.to_dict()
        assert result["position"] == "pro"
        assert len(result["arguments"]) == 1
        assert result["arguments"][0]["argument_id"] == "ARG_001"
        assert len(result["citations"]) == 1
        assert result["citations"][0]["citation_id"] == "CIT_001"

    def test_from_dict(self) -> None:
        """Test creating AdvocateReport from dictionary."""
        data = {
            "position": "pro",
            "arguments": [
                {
                    "argument_id": "ARG_001",
                    "statutory_basis": ["Art. 97 OR"],
                    "precedents": ["BGE 145 III 229"],
                    "reasoning": "Liability clearly established by statutory provision.",
                    "strength": 0.85,
                }
            ],
            "citations": [
                {
                    "citation_id": "CIT_001",
                    "type": "bge",
                    "reference": "BGE 145 III 229 E. 4.2",
                    "verified": True,
                }
            ],
        }

        report = AdvocateReport.from_dict(data)
        assert report.position == "pro"
        assert len(report.arguments) == 1
        assert report.arguments[0].argument_id == "ARG_001"

    def test_to_yaml(self) -> None:
        """Test converting AdvocateReport to YAML string."""
        report = AdvocateReport(
            position="pro",
            arguments=[
                Argument(
                    argument_id="ARG_001",
                    statutory_basis=["Art. 97 OR"],
                    precedents=[],
                    reasoning="Clear liability under contract law provisions.",
                    strength=0.75,
                )
            ],
            citations=[],
        )

        yaml_str = report.to_yaml()
        assert isinstance(yaml_str, str)
        assert "position: pro" in yaml_str
        assert "ARG_001" in yaml_str

    def test_from_yaml(self) -> None:
        """Test creating AdvocateReport from YAML string."""
        yaml_str = """
position: pro
arguments:
  - argument_id: ARG_001
    statutory_basis:
      - Art. 97 OR
    precedents:
      - BGE 145 III 229
    reasoning: Contractual liability clearly established by law.
    strength: 0.85
citations:
  - citation_id: CIT_001
    type: bge
    reference: BGE 145 III 229 E. 4.2
    verified: true
"""

        report = AdvocateReport.from_yaml(yaml_str)
        assert report.position == "pro"
        assert len(report.arguments) == 1
        assert report.arguments[0].argument_id == "ARG_001"
        assert len(report.citations) == 1

    def test_round_trip_serialization(self) -> None:
        """Test round-trip YAML serialization maintains data integrity."""
        original = AdvocateReport(
            position="anti",
            arguments=[
                Argument(
                    argument_id="ARG_002",
                    statutory_basis=["Art. 41 OR", "Art. 42 OR"],
                    precedents=["BGE 145 III 229", "BGE 144 III 43"],
                    reasoning="Tortious liability not established on these facts.",
                    strength=0.65,
                )
            ],
            citations=[
                Citation(
                    citation_id="CIT_002",
                    type="statute",
                    reference="Art. 41 OR",
                    verified=True,
                ),
                Citation(
                    citation_id="CIT_003",
                    type="doctrine",
                    reference="Gauch/Schluep, OR AT, N 123",
                    verified=False,
                ),
            ],
        )

        # Convert to YAML and back
        yaml_str = original.to_yaml()
        restored = AdvocateReport.from_yaml(yaml_str)

        # Verify all data preserved
        assert restored.position == original.position
        assert len(restored.arguments) == len(original.arguments)
        assert restored.arguments[0].argument_id == original.arguments[0].argument_id
        assert restored.arguments[0].strength == original.arguments[0].strength
        assert len(restored.citations) == len(original.citations)
