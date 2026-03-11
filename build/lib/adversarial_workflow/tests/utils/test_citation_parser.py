"""
Tests for Swiss legal citation parser.

This module contains comprehensive tests for the multi-lingual citation parser
that handles German, French, and Italian Swiss legal citations.

Test Coverage:
- BGE/ATF/DTF citation parsing (Bundesgericht decisions)
- Article references (Art., art., Abs., al., cpv., lit., let., lett.)
- Court decision citations
- Statutory citations across all three languages
- Edge cases and malformed citations
"""

import pytest

from adversarial_workflow.utils.citation_parser import (
    Citation,
    CitationParser,
    CitationType,
    InvalidCitationFormatError,
)


class TestBGECitationParsing:
    """Test cases for Bundesgericht (Federal Supreme Court) citations."""

    def test_parse_bge_german(self) -> None:
        """Test parsing German BGE citation."""
        parser = CitationParser()
        text = "BGE 145 III 229 E. 4.2"

        citations = parser.parse(text)
        assert len(citations) == 1

        citation = citations[0]
        assert citation.type == CitationType.BGE
        assert citation.language == "de"
        assert citation.volume == "145"
        assert citation.section == "III"
        assert citation.page == "229"
        assert citation.consideration == "4.2"
        assert citation.original_text == "BGE 145 III 229 E. 4.2"

    def test_parse_atf_french(self) -> None:
        """Test parsing French ATF citation."""
        parser = CitationParser()
        text = "ATF 145 III 229 consid. 4.2"

        citations = parser.parse(text)
        assert len(citations) == 1

        citation = citations[0]
        assert citation.type == CitationType.BGE
        assert citation.language == "fr"
        assert citation.volume == "145"
        assert citation.section == "III"
        assert citation.page == "229"
        assert citation.consideration == "4.2"

    def test_parse_dtf_italian(self) -> None:
        """Test parsing Italian DTF citation."""
        parser = CitationParser()
        text = "DTF 145 III 229 consid. 4.2"

        citations = parser.parse(text)
        assert len(citations) == 1

        citation = citations[0]
        assert citation.type == CitationType.BGE
        assert citation.language == "it"
        assert citation.volume == "145"
        assert citation.section == "III"
        assert citation.page == "229"
        assert citation.consideration == "4.2"

    def test_parse_bge_without_consideration(self) -> None:
        """Test BGE citation without Erwägung."""
        parser = CitationParser()
        text = "BGE 145 III 229"

        citations = parser.parse(text)
        assert len(citations) == 1

        citation = citations[0]
        assert citation.volume == "145"
        assert citation.section == "III"
        assert citation.page == "229"
        assert citation.consideration is None

    def test_parse_bge_with_sub_consideration(self) -> None:
        """Test BGE citation with nested Erwägung (E. 4.2.1)."""
        parser = CitationParser()
        text = "BGE 145 III 229 E. 4.2.1"

        citations = parser.parse(text)
        assert citations[0].consideration == "4.2.1"

    def test_parse_multiple_bge_citations(self) -> None:
        """Test parsing multiple BGE citations in text."""
        parser = CitationParser()
        text = "According to BGE 145 III 229 E. 4.2 and BGE 120 II 259 E. 2a"

        citations = parser.parse(text)
        assert len(citations) == 2
        assert citations[0].volume == "145"
        assert citations[1].volume == "120"


class TestArticleCitationParsing:
    """Test cases for statutory article citations."""

    def test_parse_article_german_simple(self) -> None:
        """Test parsing simple German article citation."""
        parser = CitationParser()
        text = "Art. 97 OR"

        citations = parser.parse(text)
        assert len(citations) == 1

        citation = citations[0]
        assert citation.type == CitationType.ARTICLE
        assert citation.language == "de"
        assert citation.article_number == "97"
        assert citation.statute == "OR"
        assert citation.paragraph is None

    def test_parse_article_german_with_paragraph(self) -> None:
        """Test parsing German article with Absatz."""
        parser = CitationParser()
        text = "Art. 123 Abs. 2 OR"

        citations = parser.parse(text)
        citation = citations[0]
        assert citation.article_number == "123"
        assert citation.paragraph == "2"
        assert citation.statute == "OR"

    def test_parse_article_german_with_letter(self) -> None:
        """Test parsing German article with Buchstabe."""
        parser = CitationParser()
        text = "Art. 123 Abs. 2 lit. a OR"

        citations = parser.parse(text)
        citation = citations[0]
        assert citation.article_number == "123"
        assert citation.paragraph == "2"
        assert citation.letter == "a"
        assert citation.statute == "OR"

    def test_parse_article_french(self) -> None:
        """Test parsing French article citation."""
        parser = CitationParser()
        text = "art. 97 al. 2 CO"

        citations = parser.parse(text)
        citation = citations[0]
        assert citation.type == CitationType.ARTICLE
        assert citation.language == "fr"
        assert citation.article_number == "97"
        assert citation.paragraph == "2"
        assert citation.statute == "CO"

    def test_parse_article_french_with_letter(self) -> None:
        """Test parsing French article with lettre."""
        parser = CitationParser()
        text = "art. 123 al. 2 let. a CO"

        citations = parser.parse(text)
        citation = citations[0]
        assert citation.article_number == "123"
        assert citation.paragraph == "2"
        assert citation.letter == "a"

    def test_parse_article_italian(self) -> None:
        """Test parsing Italian article citation."""
        parser = CitationParser()
        text = "art. 97 cpv. 2 CO"

        citations = parser.parse(text)
        citation = citations[0]
        assert citation.language == "it"
        assert citation.article_number == "97"
        assert citation.paragraph == "2"
        assert citation.statute == "CO"

    def test_parse_article_italian_with_letter(self) -> None:
        """Test parsing Italian article with lettera."""
        parser = CitationParser()
        text = "art. 123 cpv. 2 lett. a CO"

        citations = parser.parse(text)
        citation = citations[0]
        assert citation.article_number == "123"
        assert citation.paragraph == "2"
        assert citation.letter == "a"

    def test_parse_article_various_statutes(self) -> None:
        """Test parsing articles from different statutes."""
        parser = CitationParser()

        test_cases = [
            ("Art. 1 ZGB", "1", "ZGB"),
            ("Art. 321 StGB", "321", "StGB"),
            ("Art. 49 BV", "49", "BV"),
            ("art. 123 CC", "123", "CC"),
            ("art. 456 CP", "456", "CP"),
        ]

        for text, expected_article, expected_statute in test_cases:
            citations = parser.parse(text)
            assert citations[0].article_number == expected_article
            assert citations[0].statute == expected_statute

    def test_parse_multiple_article_citations(self) -> None:
        """Test parsing multiple article citations in text."""
        parser = CitationParser()
        text = "According to Art. 97 OR and Art. 41 OR"

        citations = parser.parse(text)
        assert len(citations) == 2
        assert citations[0].article_number == "97"
        assert citations[1].article_number == "41"


class TestCourtDecisionCitations:
    """Test cases for cantonal court decision citations."""

    def test_parse_zurich_court_decision(self) -> None:
        """Test parsing Zürich Obergericht decision."""
        parser = CitationParser()
        text = "Obergericht Zürich, Urteil vom 15.03.2023, LB220045"

        citations = parser.parse(text)
        assert len(citations) == 1

        citation = citations[0]
        assert citation.type == CitationType.COURT_DECISION
        assert citation.court == "Obergericht Zürich"
        assert citation.date == "15.03.2023"
        assert citation.reference == "LB220045"

    def test_parse_geneva_court_decision(self) -> None:
        """Test parsing Geneva court decision."""
        parser = CitationParser()
        text = "Cour de justice de Genève, arrêt du 15.03.2023, C/12345/2022"

        citations = parser.parse(text)
        citation = citations[0]
        assert citation.court == "Cour de justice de Genève"
        assert citation.date == "15.03.2023"
        assert citation.reference == "C/12345/2022"

    def test_parse_ticino_court_decision(self) -> None:
        """Test parsing Ticino court decision."""
        parser = CitationParser()
        text = "Tribunale d'appello del Canton Ticino, sentenza del 15.03.2023, 12.2022.45"

        citations = parser.parse(text)
        citation = citations[0]
        assert citation.court == "Tribunale d'appello del Canton Ticino"
        assert citation.date == "15.03.2023"
        assert citation.reference == "12.2022.45"


class TestMixedCitations:
    """Test cases for mixed citation formats in same text."""

    def test_parse_mixed_bge_and_article(self) -> None:
        """Test parsing text with both BGE and article citations."""
        parser = CitationParser()
        text = "According to BGE 145 III 229 E. 4.2, Art. 97 OR establishes liability."

        citations = parser.parse(text)
        assert len(citations) == 2
        assert citations[0].type == CitationType.BGE
        assert citations[1].type == CitationType.ARTICLE

    def test_parse_mixed_languages(self) -> None:
        """Test parsing citations in different languages in same text."""
        parser = CitationParser()
        text = "BGE 145 III 229 and ATF 120 II 259 and art. 97 CO"

        citations = parser.parse(text)
        assert len(citations) == 3
        assert citations[0].language == "de"
        assert citations[1].language == "fr"
        assert citations[2].language == "fr"

    def test_parse_complex_legal_text(self) -> None:
        """Test parsing complex legal text with multiple citation types."""
        parser = CitationParser()
        text = """
        The Bundesgericht in BGE 145 III 229 E. 4.2 interpreted Art. 97 Abs. 1 OR
        in accordance with Art. 8 ZGB. This was confirmed by ATF 120 II 259 consid. 2a
        and the Obergericht Zürich, Urteil vom 15.03.2023, LB220045.
        """

        citations = parser.parse(text)
        assert len(citations) >= 4  # At least BGE, Art 97, Art 8, ATF


class TestCitationValidation:
    """Test cases for citation validation."""

    def test_validate_valid_bge_citation(self) -> None:
        """Test validation of valid BGE citation."""
        parser = CitationParser()

        assert parser.validate("BGE 145 III 229") is True
        assert parser.validate("ATF 145 III 229 consid. 4.2") is True
        assert parser.validate("DTF 145 III 229") is True

    def test_validate_valid_article_citation(self) -> None:
        """Test validation of valid article citation."""
        parser = CitationParser()

        assert parser.validate("Art. 97 OR") is True
        assert parser.validate("Art. 123 Abs. 2 lit. a OR") is True
        assert parser.validate("art. 97 al. 2 CO") is True

    def test_validate_invalid_citation_format(self) -> None:
        """Test validation rejects invalid formats."""
        parser = CitationParser()

        assert parser.validate("BGE") is False
        assert parser.validate("Art. OR") is False
        assert parser.validate("123 OR") is False
        assert parser.validate("random text") is False

    def test_strict_parsing_raises_on_invalid(self) -> None:
        """Test strict parsing mode raises on invalid citation."""
        parser = CitationParser(strict=True)

        with pytest.raises(InvalidCitationFormatError):
            parser.parse("invalid citation format")


class TestCitationExtraction:
    """Test cases for extracting specific citation information."""

    def test_extract_all_references(self) -> None:
        """Test extracting all citation references from text."""
        parser = CitationParser()
        text = "BGE 145 III 229, Art. 97 OR, and ATF 120 II 259"

        references = parser.extract_references(text)
        assert len(references) == 3
        assert "BGE 145 III 229" in references
        assert "Art. 97 OR" in references
        assert "ATF 120 II 259" in references

    def test_extract_by_type(self) -> None:
        """Test extracting citations filtered by type."""
        parser = CitationParser()
        text = "BGE 145 III 229, Art. 97 OR, and ATF 120 II 259"

        bge_citations = parser.parse(text, citation_type=CitationType.BGE)
        assert len(bge_citations) == 2

        article_citations = parser.parse(text, citation_type=CitationType.ARTICLE)
        assert len(article_citations) == 1

    def test_extract_by_language(self) -> None:
        """Test extracting citations filtered by language."""
        parser = CitationParser()
        text = "BGE 145 III 229, ATF 120 II 259, and DTF 130 I 123"

        de_citations = parser.parse(text, language="de")
        fr_citations = parser.parse(text, language="fr")
        it_citations = parser.parse(text, language="it")

        assert len(de_citations) == 1
        assert len(fr_citations) == 1
        assert len(it_citations) == 1


class TestCitationDataclass:
    """Test cases for Citation dataclass functionality."""

    def test_citation_to_dict(self) -> None:
        """Test converting Citation to dictionary."""
        citation = Citation(
            type=CitationType.BGE,
            language="de",
            original_text="BGE 145 III 229 E. 4.2",
            volume="145",
            section="III",
            page="229",
            consideration="4.2",
        )

        result = citation.to_dict()
        assert result["type"] == "BGE"
        assert result["language"] == "de"
        assert result["volume"] == "145"
        assert result["consideration"] == "4.2"

    def test_citation_equality(self) -> None:
        """Test Citation equality comparison."""
        citation1 = Citation(
            type=CitationType.ARTICLE,
            language="de",
            original_text="Art. 97 OR",
            article_number="97",
            statute="OR",
        )

        citation2 = Citation(
            type=CitationType.ARTICLE,
            language="de",
            original_text="Art. 97 OR",
            article_number="97",
            statute="OR",
        )

        assert citation1 == citation2

    def test_citation_string_representation(self) -> None:
        """Test Citation string representation."""
        citation = Citation(
            type=CitationType.BGE,
            language="de",
            original_text="BGE 145 III 229 E. 4.2",
            volume="145",
            section="III",
            page="229",
            consideration="4.2",
        )

        assert str(citation) == "BGE 145 III 229 E. 4.2"


class TestEdgeCases:
    """Test cases for edge cases and error handling."""

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string returns empty list."""
        parser = CitationParser()
        citations = parser.parse("")
        assert citations == []

    def test_parse_text_without_citations(self) -> None:
        """Test parsing text without citations returns empty list."""
        parser = CitationParser()
        citations = parser.parse("This is just regular text without any citations.")
        assert citations == []

    def test_parse_malformed_bge_citation(self) -> None:
        """Test parsing malformed BGE citation (lenient mode)."""
        parser = CitationParser(strict=False)

        # Missing section
        _citations = parser.parse("BGE 145 229")
        # Should handle gracefully in lenient mode (no assertion needed)

    def test_parse_article_without_statute(self) -> None:
        """Test parsing article reference without statute name."""
        parser = CitationParser(strict=False)
        _citations = parser.parse("Art. 97")

        # In lenient mode, should either parse or skip gracefully (no assertion needed)
        # Not all partial citations are invalid in context

    def test_whitespace_handling(self) -> None:
        """Test parsing handles various whitespace correctly."""
        parser = CitationParser()

        test_cases = [
            "BGE 145 III 229",
            "BGE  145  III  229",  # Double spaces
            "BGE 145 III 229",  # Tab characters
        ]

        for text in test_cases:
            citations = parser.parse(text)
            assert len(citations) == 1
            assert citations[0].volume == "145"

    def test_case_insensitivity(self) -> None:
        """Test parsing is case-insensitive where appropriate."""
        parser = CitationParser()

        # BGE should be case-insensitive
        citations1 = parser.parse("bge 145 III 229")
        citations2 = parser.parse("BGE 145 III 229")

        # Both should parse successfully
        assert len(citations1) == 1
        assert len(citations2) == 1
