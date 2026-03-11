"""Tests for UserQueryPackage data structure.

Test-Driven Development (TDD) for UserQueryPackage schema implementation.
Coverage target: ≥90%
"""

import pytest

from adversarial_workflow.data_structures.user_query_package import UserQueryPackage


class TestUserQueryPackageSchema:
    """Test UserQueryPackage schema structure and validation."""

    def test_valid_federal_query_minimal(self) -> None:
        """Test valid federal query with minimal required fields."""
        data = {
            "query_text": "Vertragshaftung gemäss Art. 97 OR - analysis needed",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "de", "confidence": 0.98},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-001",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.query_text == data["query_text"]
        assert query_package.jurisdiction.level == "federal"

    def test_valid_cantonal_query_zurich(self) -> None:
        """Test valid cantonal query for Zürich."""
        data = {
            "query_text": "Cantonal tax law implications for corporate restructuring",
            "jurisdiction": {"level": "cantonal", "canton_code": "ZH"},
            "language": {"detected": "en", "confidence": 0.96},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-002",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.jurisdiction.level == "cantonal"
        assert query_package.jurisdiction.canton_code == "ZH"

    def test_valid_cantonal_query_geneva_french(self) -> None:
        """Test valid cantonal query for Geneva in French."""
        data = {
            "query_text": "Responsabilité contractuelle selon l'art. 97 CO - analyse requise",
            "jurisdiction": {"level": "cantonal", "canton_code": "GE"},
            "language": {"detected": "fr", "confidence": 0.99},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-003",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.language.detected == "fr"
        assert query_package.jurisdiction.canton_code == "GE"

    def test_valid_cantonal_query_ticino_italian(self) -> None:
        """Test valid cantonal query for Ticino in Italian."""
        data = {
            "query_text": "Responsabilità contrattuale secondo l'art. 97 CO - analisi necessaria",
            "jurisdiction": {"level": "cantonal", "canton_code": "TI"},
            "language": {"detected": "it", "confidence": 0.97},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-004",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.language.detected == "it"
        assert query_package.jurisdiction.canton_code == "TI"


class TestQueryTextValidation:
    """Test query_text field validation."""

    def test_query_text_minimum_length(self) -> None:
        """Test query_text must be at least 20 characters."""
        data = {
            "query_text": "Short query",  # Only 11 characters
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-005",
            },
        }
        with pytest.raises(ValueError, match="query_text must be at least 20 characters"):
            UserQueryPackage.from_dict(data)

    def test_query_text_exactly_20_characters(self) -> None:
        """Test query_text with exactly 20 characters is valid."""
        data = {
            "query_text": "Valid query text!!!!",  # Exactly 20 characters
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-006",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.query_text == data["query_text"]

    def test_query_text_empty_string(self) -> None:
        """Test query_text cannot be empty string."""
        data = {
            "query_text": "",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-007",
            },
        }
        with pytest.raises(ValueError, match="query_text cannot be empty"):
            UserQueryPackage.from_dict(data)

    def test_query_text_whitespace_only(self) -> None:
        """Test query_text cannot be whitespace only."""
        data = {
            "query_text": "                    ",  # 20 spaces
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-008",
            },
        }
        with pytest.raises(ValueError, match="query_text cannot be whitespace only"):
            UserQueryPackage.from_dict(data)


class TestJurisdictionValidation:
    """Test jurisdiction field validation."""

    def test_jurisdiction_level_federal(self) -> None:
        """Test federal jurisdiction level."""
        data = {
            "query_text": "Federal law question regarding Art. 97 OR liability",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-009",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.jurisdiction.level == "federal"
        assert query_package.jurisdiction.canton_code is None

    def test_jurisdiction_level_cantonal_requires_canton_code(self) -> None:
        """Test cantonal jurisdiction requires canton_code."""
        data = {
            "query_text": "Cantonal law question without canton specified",
            "jurisdiction": {"level": "cantonal"},  # Missing canton_code
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-010",
            },
        }
        with pytest.raises(ValueError, match="cantonal jurisdiction requires canton_code"):
            UserQueryPackage.from_dict(data)

    def test_jurisdiction_invalid_level(self) -> None:
        """Test invalid jurisdiction level."""
        data = {
            "query_text": "Question with invalid jurisdiction level",
            "jurisdiction": {"level": "municipal"},  # Invalid level
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-011",
            },
        }
        with pytest.raises(ValueError, match="level must be 'federal' or 'cantonal'"):
            UserQueryPackage.from_dict(data)

    @pytest.mark.parametrize(
        "canton_code",
        ["ZH", "BE", "GE", "BS", "VD", "TI"],
    )
    def test_jurisdiction_valid_canton_codes(self, canton_code: str) -> None:
        """Test all valid canton codes (v1.0 supported cantons)."""
        data = {
            "query_text": f"Cantonal law question for canton {canton_code}",
            "jurisdiction": {"level": "cantonal", "canton_code": canton_code},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": f"test-session-{canton_code}",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.jurisdiction.canton_code == canton_code

    def test_jurisdiction_invalid_canton_code(self) -> None:
        """Test invalid canton code."""
        data = {
            "query_text": "Cantonal law question for invalid canton",
            "jurisdiction": {"level": "cantonal", "canton_code": "XX"},  # Invalid
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-012",
            },
        }
        with pytest.raises(ValueError, match="canton_code must be one of"):
            UserQueryPackage.from_dict(data)


class TestLanguageValidation:
    """Test language detection validation."""

    @pytest.mark.parametrize(
        "language_code",
        ["de", "fr", "it", "en"],
    )
    def test_language_valid_codes(self, language_code: str) -> None:
        """Test all valid language codes (DE/FR/IT/EN)."""
        data = {
            "query_text": "Valid query in any supported language",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": language_code, "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": f"test-session-{language_code}",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.language.detected == language_code

    def test_language_invalid_code(self) -> None:
        """Test invalid language code."""
        data = {
            "query_text": "Query with invalid language code",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "es", "confidence": 0.95},  # Spanish not supported
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-013",
            },
        }
        with pytest.raises(ValueError, match="detected language must be one of"):
            UserQueryPackage.from_dict(data)

    def test_language_confidence_minimum(self) -> None:
        """Test language confidence must be ≥0.95 (95% accuracy target)."""
        data = {
            "query_text": "Query with low confidence language detection",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.94},  # Below threshold
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-014",
            },
        }
        with pytest.raises(ValueError, match="confidence must be at least 0.95"):
            UserQueryPackage.from_dict(data)

    def test_language_confidence_exactly_95_percent(self) -> None:
        """Test language confidence exactly at 95% threshold."""
        data = {
            "query_text": "Query with exactly 95% confidence",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-015",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.language.confidence == 0.95

    def test_language_confidence_above_100_percent(self) -> None:
        """Test language confidence cannot exceed 1.0 (100%)."""
        data = {
            "query_text": "Query with confidence above 100%",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 1.1},  # Above max
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-016",
            },
        }
        with pytest.raises(ValueError, match="confidence must be between 0.95 and 1.0"):
            UserQueryPackage.from_dict(data)


class TestMetadataValidation:
    """Test metadata field validation."""

    def test_metadata_valid_timestamp_iso8601(self) -> None:
        """Test valid ISO 8601 timestamp format."""
        data = {
            "query_text": "Query with valid ISO 8601 timestamp",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-017",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.metadata.timestamp == "2024-01-05T10:30:00Z"

    def test_metadata_invalid_timestamp_format(self) -> None:
        """Test invalid timestamp format."""
        data = {
            "query_text": "Query with invalid timestamp format",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "05/01/2024 10:30",  # Wrong format
                "session_id": "test-session-018",
            },
        }
        with pytest.raises(ValueError, match="timestamp must be ISO 8601 format"):
            UserQueryPackage.from_dict(data)

    def test_metadata_valid_session_id_uuid(self) -> None:
        """Test valid UUID session_id."""
        data = {
            "query_text": "Query with valid UUID session ID",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        assert query_package.metadata.session_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_metadata_session_id_non_empty(self) -> None:
        """Test session_id cannot be empty."""
        data = {
            "query_text": "Query with empty session ID",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {"timestamp": "2024-01-05T10:30:00Z", "session_id": ""},
        }
        with pytest.raises(ValueError, match="session_id cannot be empty"):
            UserQueryPackage.from_dict(data)


class TestYAMLSerialization:
    """Test YAML serialization and deserialization."""

    def test_to_yaml_basic(self) -> None:
        """Test serialization to YAML format."""
        data = {
            "query_text": "Vertragshaftung gemäss Art. 97 OR",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "de", "confidence": 0.98},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-019",
            },
        }
        query_package = UserQueryPackage.from_dict(data)
        yaml_output = query_package.to_yaml()
        assert "query_text:" in yaml_output
        assert "jurisdiction:" in yaml_output
        assert "level: federal" in yaml_output

    def test_from_yaml_basic(self) -> None:
        """Test deserialization from YAML format."""
        yaml_input = """
query_text: "Vertragshaftung gemäss Art. 97 OR"
jurisdiction:
  level: federal
language:
  detected: de
  confidence: 0.98
metadata:
  timestamp: "2024-01-05T10:30:00Z"
  session_id: "test-session-020"
"""
        query_package = UserQueryPackage.from_yaml(yaml_input)
        assert query_package.query_text == "Vertragshaftung gemäss Art. 97 OR"
        assert query_package.jurisdiction.level == "federal"

    def test_round_trip_serialization(self) -> None:
        """Test round-trip serialization: dict → YAML → dict."""
        original_data = {
            "query_text": "Cantonal tax law question for Zürich canton",
            "jurisdiction": {"level": "cantonal", "canton_code": "ZH"},
            "language": {"detected": "en", "confidence": 0.96},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-021",
            },
        }
        query_package = UserQueryPackage.from_dict(original_data)
        yaml_output = query_package.to_yaml()
        restored_package = UserQueryPackage.from_yaml(yaml_output)
        assert restored_package.to_dict() == original_data


class TestRequiredFields:
    """Test that all required fields are enforced."""

    def test_missing_query_text(self) -> None:
        """Test missing query_text field."""
        data = {
            # Missing query_text
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-022",
            },
        }
        with pytest.raises(ValueError, match="query_text is required"):
            UserQueryPackage.from_dict(data)

    def test_missing_jurisdiction(self) -> None:
        """Test missing jurisdiction field."""
        data = {
            "query_text": "Query without jurisdiction specified",
            # Missing jurisdiction
            "language": {"detected": "en", "confidence": 0.95},
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-023",
            },
        }
        with pytest.raises(ValueError, match="jurisdiction is required"):
            UserQueryPackage.from_dict(data)

    def test_missing_language(self) -> None:
        """Test missing language field."""
        data = {
            "query_text": "Query without language detection",
            "jurisdiction": {"level": "federal"},
            # Missing language
            "metadata": {
                "timestamp": "2024-01-05T10:30:00Z",
                "session_id": "test-session-024",
            },
        }
        with pytest.raises(ValueError, match="language is required"):
            UserQueryPackage.from_dict(data)

    def test_missing_metadata(self) -> None:
        """Test missing metadata field."""
        data = {
            "query_text": "Query without metadata",
            "jurisdiction": {"level": "federal"},
            "language": {"detected": "en", "confidence": 0.95},
            # Missing metadata
        }
        with pytest.raises(ValueError, match="metadata is required"):
            UserQueryPackage.from_dict(data)
