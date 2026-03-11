"""
Multi-lingual Swiss legal citation parser.

This module provides comprehensive parsing and validation of Swiss legal citations
across German, French, and Italian languages, supporting:

- BGE/ATF/DTF citations (Bundesgericht/Federal Supreme Court decisions)
- Article references with complex structures (Art., Abs./al./cpv., lit./let./lett.)
- Court decision citations (cantonal and federal courts)
- Multi-lingual terminology consistency

Citation Types:
- BGE: Federal Supreme Court decisions (German: BGE, French: ATF, Italian: DTF)
- ARTICLE: Statutory article references with optional paragraph and letter components
- COURT_DECISION: Court decisions with date and reference numbers

Languages Supported:
- German (de): BGE, Art., Abs., lit., E.
- French (fr): ATF, art., al., let., consid.
- Italian (it): DTF, art., cpv., lett., consid.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CitationType(Enum):
    """Types of legal citations supported by the parser."""

    BGE = "BGE"  # Bundesgericht/ATF/DTF decisions
    ARTICLE = "ARTICLE"  # Statutory article references
    COURT_DECISION = "COURT_DECISION"  # Court decisions


class CitationParseError(Exception):
    """Base exception for citation parsing errors."""

    pass


class InvalidCitationFormatError(CitationParseError):
    """Raised when citation format is invalid and parser is in strict mode."""

    pass


@dataclass
class Citation:
    """
    Represents a parsed legal citation.

    Attributes:
        type: Type of citation (BGE, ARTICLE, COURT_DECISION)
        language: Language of citation (de, fr, it, en)
        original_text: Original citation text as found in source

        # BGE-specific fields
        volume: BGE volume number
        section: BGE section (I, Ia, II, III, IV, V, VI)
        page: Starting page number
        consideration: Specific consideration/reasoning section (Erwägung)

        # Article-specific fields
        article_number: Article number
        statute: Statute code (OR, ZGB, StGB, BV, etc.)
        paragraph: Paragraph/Absatz/alinéa/capoverso number
        letter: Letter/Buchstabe/lettre/lettera designation

        # Court decision fields
        court: Court name
        date: Decision date
        reference: Case reference number
    """

    type: CitationType
    language: str
    original_text: str

    # BGE fields
    volume: str | None = None
    section: str | None = None
    page: str | None = None
    consideration: str | None = None

    # Article fields
    article_number: str | None = None
    statute: str | None = None
    paragraph: str | None = None
    letter: str | None = None

    # Court decision fields
    court: str | None = None
    date: str | None = None
    reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert citation to dictionary representation."""
        result = {
            "type": self.type.value,
            "language": self.language,
            "original_text": self.original_text,
        }

        # Add BGE fields if present
        if self.volume is not None:
            result["volume"] = self.volume
        if self.section is not None:
            result["section"] = self.section
        if self.page is not None:
            result["page"] = self.page
        if self.consideration is not None:
            result["consideration"] = self.consideration

        # Add Article fields if present
        if self.article_number is not None:
            result["article_number"] = self.article_number
        if self.statute is not None:
            result["statute"] = self.statute
        if self.paragraph is not None:
            result["paragraph"] = self.paragraph
        if self.letter is not None:
            result["letter"] = self.letter

        # Add Court decision fields if present
        if self.court is not None:
            result["court"] = self.court
        if self.date is not None:
            result["date"] = self.date
        if self.reference is not None:
            result["reference"] = self.reference

        return result

    def __str__(self) -> str:
        """Return original citation text."""
        return self.original_text


class CitationParser:
    """
    Multi-lingual Swiss legal citation parser.

    Parses and validates legal citations across German, French, and Italian,
    supporting BGE decisions, statutory articles, and court decisions.

    Args:
        strict: If True, raise InvalidCitationFormatError for invalid citations.
                If False, skip invalid citations gracefully.
    """

    # BGE patterns for all three languages
    BGE_PATTERNS = {
        "de": re.compile(
            r"\b(BGE)\s+(\d+)\s+([IV]+)\s+(\d+)(?:\s+E\.\s+([\d.]+))?(?:\s+S\.\s+(\d+))?\b",
            re.IGNORECASE,
        ),
        "fr": re.compile(
            r"\b(ATF)\s+(\d+)\s+([IV]+)\s+(\d+)(?:\s+consid\.\s+([\d.]+))?(?:\s+p\.\s+(\d+))?\b",
            re.IGNORECASE,
        ),
        "it": re.compile(
            r"\b(DTF)\s+(\d+)\s+([IV]+)\s+(\d+)(?:\s+consid\.\s+([\d.]+))?(?:\s+pag\.\s+(\d+))?\b",
            re.IGNORECASE,
        ),
    }

    # Article patterns for all three languages
    ARTICLE_PATTERNS = {
        "de": re.compile(
            r"\bArt\.\s+(\d+)(?:\s+Abs\.\s+(\d+))?(?:\s+lit\.\s+([a-z]))?\s+([A-Za-z]{2,5})\b"
        ),
        "fr": re.compile(
            r"\bart\.\s+(\d+)(?:\s+al\.\s+(\d+))?(?:\s+let\.\s+([a-z]))?\s+([A-Za-z]{2,5})\b"
        ),
        "it": re.compile(
            r"\bart\.\s+(\d+)(?:\s+cpv\.\s+(\d+))?(?:\s+lett\.\s+([a-z]))?\s+([A-Za-z]{2,5})\b"
        ),
    }

    # Court decision patterns
    COURT_DECISION_PATTERNS = [
        # German courts
        re.compile(
            r"(Obergericht\s+\w+|Kantonsgericht\s+\w+),\s+Urteil\s+vom\s+([\d.]+),\s+([\w\d/]+)",
            re.IGNORECASE,
        ),
        # French courts
        re.compile(
            r"(Cour\s+de\s+justice\s+de\s+\w+|Tribunal\s+[^,]+),\s+arrêt\s+du\s+([\d.]+),\s+([\w\d/]+)",
            re.IGNORECASE,
        ),
        # Italian courts
        re.compile(
            r"(Tribunale\s+d'appello\s+del\s+Canton\s+\w+|Tribunale\s+[^,]+),\s+sentenza\s+del\s+([\d.]+),\s+([\w\d./]+)",
            re.IGNORECASE,
        ),
    ]

    def __init__(self, strict: bool = False) -> None:
        """
        Initialize citation parser.

        Args:
            strict: If True, raise exceptions for invalid citations
        """
        self.strict = strict

    def parse(
        self,
        text: str,
        citation_type: CitationType | None = None,
        language: str | None = None,
    ) -> list[Citation]:
        """
        Parse legal citations from text.

        Args:
            text: Text containing legal citations
            citation_type: Optional filter by citation type
            language: Optional filter by language (de, fr, it)

        Returns:
            List of parsed Citation objects

        Raises:
            InvalidCitationFormatError: If strict mode and invalid citation found
        """
        if not text:
            return []

        citations: list[Citation] = []

        # Parse BGE citations if not filtered out
        if citation_type is None or citation_type == CitationType.BGE:
            citations.extend(self._parse_bge_citations(text, language))

        # Parse article citations if not filtered out
        if citation_type is None or citation_type == CitationType.ARTICLE:
            citations.extend(self._parse_article_citations(text, language))

        # Parse court decisions if not filtered out
        if citation_type is None or citation_type == CitationType.COURT_DECISION:
            citations.extend(self._parse_court_decisions(text))

        # Apply language filter if specified
        if language is not None:
            citations = [c for c in citations if c.language == language]

        # In strict mode, raise error if no valid citations found in non-empty text
        if self.strict and not citations and text.strip():
            raise InvalidCitationFormatError(f"No valid citations found in text: {text}")

        return citations

    def validate(self, text: str) -> bool:
        """
        Validate if text contains valid legal citation.

        Args:
            text: Text to validate

        Returns:
            True if text contains at least one valid citation, False otherwise
        """
        try:
            citations = self.parse(text, citation_type=None, language=None)
            return len(citations) > 0
        except CitationParseError:
            return False

    def extract_references(self, text: str) -> list[str]:
        """
        Extract all citation reference strings from text.

        Args:
            text: Text containing citations

        Returns:
            List of citation strings
        """
        citations = self.parse(text)
        return [citation.original_text for citation in citations]

    def _parse_bge_citations(self, text: str, language_filter: str | None = None) -> list[Citation]:
        """Parse BGE/ATF/DTF citations from text."""
        citations: list[Citation] = []

        for lang, pattern in self.BGE_PATTERNS.items():
            # Skip if language filter specified and doesn't match
            if language_filter is not None and lang != language_filter:
                continue

            for match in pattern.finditer(text):
                _ = match.group(1)  # BGE/ATF/DTF prefix (captured but not needed)
                volume = match.group(2)
                section = match.group(3)
                page = match.group(4)
                consideration = (
                    match.group(5) if match.lastindex is not None and match.lastindex >= 5 else None
                )

                # Extract original text from match
                original_text = match.group(0)

                citation = Citation(
                    type=CitationType.BGE,
                    language=lang,
                    original_text=original_text,
                    volume=volume,
                    section=section,
                    page=page,
                    consideration=consideration,
                )

                citations.append(citation)

        return citations

    def _parse_article_citations(
        self, text: str, language_filter: str | None = None
    ) -> list[Citation]:
        """Parse statutory article citations from text."""
        citations: list[Citation] = []
        matched_positions: set = set()  # Track (start, end) positions to avoid duplicates

        # Language-specific keyword detection for routing
        # This prevents Italian "cpv." from matching French pattern
        language_hints = {
            "de": r"\bAbs\.",  # German: Absatz
            "fr": r"\bal\.",  # French: alinéa
            "it": r"\bcpv\.",  # Italian: capoverso
        }

        # Determine language priority based on keyword presence
        lang_priority = []
        for lang, keyword_pattern in language_hints.items():
            if re.search(keyword_pattern, text):
                lang_priority.append(lang)

        # Add remaining languages after keyword-detected ones
        for lang in self.ARTICLE_PATTERNS.keys():
            if lang not in lang_priority:
                lang_priority.append(lang)

        # Try patterns in priority order (keyword-detected first)
        for lang in lang_priority:
            # Skip if language filter specified and doesn't match
            if language_filter is not None and lang != language_filter:
                continue

            pattern = self.ARTICLE_PATTERNS[lang]
            for match in pattern.finditer(text):
                # Skip if this position was already matched by another language
                position = (match.start(), match.end())
                if position in matched_positions:
                    continue

                matched_positions.add(position)

                article_number = match.group(1)
                paragraph = (
                    match.group(2)
                    if match.lastindex is not None and match.lastindex >= 2 and match.group(2)
                    else None
                )
                letter = (
                    match.group(3)
                    if match.lastindex is not None and match.lastindex >= 3 and match.group(3)
                    else None
                )
                statute = (
                    match.group(4) if match.lastindex is not None and match.lastindex >= 4 else None
                )

                # Extract original text from match
                original_text = match.group(0)

                citation = Citation(
                    type=CitationType.ARTICLE,
                    language=lang,
                    original_text=original_text,
                    article_number=article_number,
                    statute=statute,
                    paragraph=paragraph,
                    letter=letter,
                )

                citations.append(citation)

        return citations

    def _parse_court_decisions(self, text: str) -> list[Citation]:
        """Parse court decision citations from text."""
        citations: list[Citation] = []

        for pattern in self.COURT_DECISION_PATTERNS:
            for match in pattern.finditer(text):
                court = match.group(1)
                date = match.group(2)
                reference = match.group(3)

                # Extract original text from match
                original_text = match.group(0)

                # Detect language based on court keywords
                lang = "de"  # default
                if any(keyword in court.lower() for keyword in ["cour", "tribunal", "arrêt"]):
                    lang = "fr"
                elif any(keyword in court.lower() for keyword in ["tribunale", "sentenza"]):
                    lang = "it"

                citation = Citation(
                    type=CitationType.COURT_DECISION,
                    language=lang,
                    original_text=original_text,
                    court=court,
                    date=date,
                    reference=reference,
                )

                citations.append(citation)

        return citations
