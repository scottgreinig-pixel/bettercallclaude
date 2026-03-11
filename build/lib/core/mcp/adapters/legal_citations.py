"""
Legal Citations MCP Adapter

Provides high-level interface to Legal Citations MCP server for
citation validation, formatting, conversion, and parsing.

Supports Swiss legal citation formats:
- BGE/ATF/DTF (Federal Supreme Court decisions)
- Statutory references (Art. X OR, ZGB, StGB, etc.)
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

from ..protocol import MCPClient, MCPInvocationError

logger = logging.getLogger(__name__)


@dataclass
class CitationValidationResult:
    """Result of citation validation."""

    valid: bool
    citation_type: str  # "bge", "statutory", or "unknown"
    normalized: str  # Normalized citation format
    components: dict[str, Any]  # Parsed components
    errors: list[str]  # Validation errors
    warnings: list[str]  # Non-critical warnings


@dataclass
class FormattedCitation:
    """Result of citation formatting."""

    original: str
    formatted: str
    language: str
    citation_type: str
    full_reference: str | None  # Full name if requested


@dataclass
class ConvertedCitation:
    """Result of citation conversion."""

    original: str
    source_language: str
    target_language: str
    converted: str
    full_reference: str | None
    all_translations: dict[str, str]


@dataclass
class ParsedCitation:
    """Result of citation parsing."""

    original: str
    citation_type: str
    language: str
    components: dict[str, Any]
    is_valid: bool
    suggestions: list[str]


class LegalCitationsAdapter:
    """
    High-level adapter for Legal Citations MCP server.

    Provides Swiss legal citation services:
    - Validation: Check citation format and components
    - Formatting: Format citations to specific language
    - Conversion: Convert citations between languages
    - Parsing: Extract citation components

    Example:
        adapter = LegalCitationsAdapter(
            command=["node", "mcp-servers/legal-citations/dist/index.js"]
        )

        async with adapter:
            # Validate citation
            result = await adapter.validate("BGE 147 IV 73")
            if result.valid:
                print(f"Valid {result.citation_type} citation")

            # Format to French
            formatted = await adapter.format("BGE 147 IV 73", "fr")
            print(f"French: {formatted.formatted}")  # "ATF 147 IV 73"

            # Parse citation components
            parsed = await adapter.parse("Art. 97 OR")
            print(f"Article: {parsed.components.get('article')}")
    """

    def __init__(
        self,
        command: list[str],
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize Legal Citations adapter.

        Args:
            command: Command to start Legal Citations MCP server
            env: Optional environment variables
            timeout: Request timeout in seconds
        """
        self.client = MCPClient(
            command=command, server_id="legal_citations", env=env, timeout=timeout
        )

    async def connect(self) -> None:
        """Connect to Legal Citations MCP server."""
        await self.client.connect()
        await self.client.initialize()
        logger.info("Legal Citations adapter connected and initialized")

    async def disconnect(self) -> None:
        """Disconnect from Legal Citations MCP server."""
        await self.client.disconnect()

    async def validate(self, citation: str) -> CitationValidationResult:
        """
        Validate a Swiss legal citation.

        Args:
            citation: The citation to validate (e.g., "BGE 147 IV 73", "Art. 97 OR")

        Returns:
            CitationValidationResult with validation details

        Raises:
            MCPInvocationError: If validation fails
        """
        try:
            result = await self.client.invoke_tool("validate_citation", {"citation": citation})

            # Parse the JSON response from content
            content = result.get("content", [])
            if content and isinstance(content, list):
                text_content = content[0].get("text", "{}")
                data = json.loads(text_content)
            else:
                data = result

            return CitationValidationResult(
                valid=data.get("valid", False),
                citation_type=data.get("type", "unknown"),
                normalized=data.get("normalized", citation),
                components=data.get("components", {}),
                errors=data.get("errors", []),
                warnings=data.get("warnings", []),
            )

        except MCPInvocationError as e:
            logger.error(f"Citation validation failed: {e}")
            raise

    async def format(
        self,
        citation: str,
        target_language: str,
        full_statute_name: bool = False,
    ) -> FormattedCitation:
        """
        Format a Swiss legal citation to a specific language.

        Args:
            citation: The citation to format
            target_language: Target language ("de", "fr", "it", "en")
            full_statute_name: Include full statute name in parentheses

        Returns:
            FormattedCitation with formatting result

        Raises:
            MCPInvocationError: If formatting fails
            ValueError: If target_language is invalid
        """
        if target_language.lower() not in ["de", "fr", "it", "en"]:
            raise ValueError(
                f"Invalid target_language: {target_language}. " "Must be one of: de, fr, it, en"
            )

        try:
            result = await self.client.invoke_tool(
                "format_citation",
                {
                    "citation": citation,
                    "targetLanguage": target_language.lower(),
                    "fullStatuteName": full_statute_name,
                },
            )

            content = result.get("content", [])
            if content and isinstance(content, list):
                text_content = content[0].get("text", "{}")
                data = json.loads(text_content)
            else:
                data = result

            return FormattedCitation(
                original=data.get("original", citation),
                formatted=data.get("formatted", citation),
                language=data.get("language", target_language),
                citation_type=data.get("type", "unknown"),
                full_reference=data.get("fullReference"),
            )

        except MCPInvocationError as e:
            logger.error(f"Citation formatting failed: {e}")
            raise

    async def convert(
        self,
        citation: str,
        target_language: str,
        full_statute_name: bool = False,
    ) -> ConvertedCitation:
        """
        Convert a citation from one language to another.

        Auto-detects source language and converts to target language.

        Args:
            citation: The citation to convert
            target_language: Target language ("de", "fr", "it", "en")
            full_statute_name: Include full statute name

        Returns:
            ConvertedCitation with conversion result and all translations

        Raises:
            MCPInvocationError: If conversion fails
            ValueError: If target_language is invalid
        """
        if target_language.lower() not in ["de", "fr", "it", "en"]:
            raise ValueError(
                f"Invalid target_language: {target_language}. " "Must be one of: de, fr, it, en"
            )

        try:
            result = await self.client.invoke_tool(
                "convert_citation",
                {
                    "citation": citation,
                    "targetLanguage": target_language.lower(),
                    "fullStatuteName": full_statute_name,
                },
            )

            content = result.get("content", [])
            if content and isinstance(content, list):
                text_content = content[0].get("text", "{}")
                data = json.loads(text_content)
            else:
                data = result

            return ConvertedCitation(
                original=data.get("original", citation),
                source_language=data.get("sourceLanguage", ""),
                target_language=data.get("targetLanguage", target_language),
                converted=data.get("converted", citation),
                full_reference=data.get("fullReference"),
                all_translations=data.get("allTranslations", {}),
            )

        except MCPInvocationError as e:
            logger.error(f"Citation conversion failed: {e}")
            raise

    async def parse(self, citation: str) -> ParsedCitation:
        """
        Parse a Swiss legal citation and extract components.

        Args:
            citation: The citation to parse

        Returns:
            ParsedCitation with extracted components

        Raises:
            MCPInvocationError: If parsing fails
        """
        try:
            result = await self.client.invoke_tool("parse_citation", {"citation": citation})

            content = result.get("content", [])
            if content and isinstance(content, list):
                text_content = content[0].get("text", "{}")
                data = json.loads(text_content)
            else:
                data = result

            return ParsedCitation(
                original=data.get("original", citation),
                citation_type=data.get("type", "unknown"),
                language=data.get("language", ""),
                components=data.get("components", {}),
                is_valid=data.get("isValid", False),
                suggestions=data.get("suggestions", []),
            )

        except MCPInvocationError as e:
            logger.error(f"Citation parsing failed: {e}")
            raise

    async def verify(self, citation: str) -> dict[str, Any]:
        """
        Verify a citation and return verification result.

        This method is used by the ResearcherAgent for citation verification.

        Args:
            citation: The citation to verify

        Returns:
            Dict with verification result:
            {
                "verified": bool,
                "formatted": str,
                "is_current": bool,
                "court": str,
                "issues": List[str]
            }
        """
        try:
            # Validate first
            validation = await self.validate(citation)

            # Parse for additional details
            parsed = await self.parse(citation)

            # Determine court from citation type
            court = ""
            if parsed.citation_type == "bge":
                court = "Bundesgericht"
            elif parsed.components.get("court"):
                court = parsed.components["court"]

            return {
                "verified": validation.valid,
                "formatted": validation.normalized,
                "is_current": True,  # Would check against a database in production
                "court": court,
                "issues": validation.errors + validation.warnings,
            }

        except MCPInvocationError as e:
            logger.error(f"Citation verification failed: {e}")
            return {
                "verified": False,
                "formatted": citation,
                "is_current": False,
                "court": "",
                "issues": [str(e)],
            }

    async def get_provision_text(
        self,
        statute: str,
        article: str,
        paragraph: str | None = None,
        language: str = "de",
    ) -> dict[str, Any]:
        """
        Get the text of a statutory provision from Fedlex.

        Args:
            statute: Statute abbreviation (ZGB, OR, StGB, etc.)
            article: Article number
            paragraph: Paragraph/Absatz number (optional)
            language: Language for the text (de, fr, it, en)

        Returns:
            Dict with provision data including:
            - statute: Statute abbreviation
            - article: Article number
            - paragraph: Paragraph number (if specified)
            - text: The provision text
            - language: Language of the text
            - fedlex_url: URL to Fedlex source
            - sr_number: SR number of the statute

        Raises:
            MCPInvocationError: If retrieval fails
        """
        params: dict[str, Any] = {
            "statute": statute.upper(),
            "article": article,
            "language": language.lower(),
        }

        if paragraph:
            params["paragraph"] = paragraph

        try:
            result = await self.client.invoke_tool("get_provision_text", params)

            content = result.get("content", [])
            if content and isinstance(content, list):
                text_content = content[0].get("text", "{}")
                data: dict[str, Any] = json.loads(text_content)
                return data
            return dict(result)

        except MCPInvocationError as e:
            logger.error(f"Provision text retrieval failed: {e}")
            raise

    async def extract_citations(
        self,
        text: str,
        include_statutes: bool = True,
        include_decisions: bool = True,
    ) -> dict[str, Any]:
        """
        Extract legal citations from a text document.

        Args:
            text: The text to analyze for citations
            include_statutes: Extract statutory citations (Art. X OR)
            include_decisions: Extract decision citations (BGE/ATF/DTF)

        Returns:
            Dict with extraction results including:
            - citations: List of extracted citations with positions
            - statistics: Summary statistics (count by type)
            - unique_citations: Deduplicated list

            Each citation includes:
            - citation: The citation text
            - type: Citation type (bge, atf, dtf, statute)
            - position: Start and end positions in text
            - normalized: Normalized form
            - valid: Whether citation is valid

        Raises:
            MCPInvocationError: If extraction fails
        """
        try:
            result = await self.client.invoke_tool(
                "extract_citations",
                {
                    "text": text,
                    "includeStatutes": include_statutes,
                    "includeDecisions": include_decisions,
                },
            )

            content = result.get("content", [])
            if content and isinstance(content, list):
                text_content = content[0].get("text", "{}")
                data: dict[str, Any] = json.loads(text_content)
                return data
            return dict(result)

        except MCPInvocationError as e:
            logger.error(f"Citation extraction failed: {e}")
            raise

    async def standardize_document_citations(
        self,
        text: str,
        target_language: str = "de",
        full_statute_names: bool = False,
    ) -> dict[str, Any]:
        """
        Standardize all citations in a document to consistent format.

        Args:
            text: The document text with citations
            target_language: Target language for citations (de, fr, it)
            full_statute_names: Include full statute names

        Returns:
            Dict with standardization results including:
            - original_text: The input text
            - standardized_text: Text with standardized citations
            - changes_made: List of changes applied
            - citation_count: Number of citations processed

            Each change includes:
            - original: Original citation
            - standardized: Standardized form
            - position: Position in original text

        Raises:
            MCPInvocationError: If standardization fails
        """
        try:
            result = await self.client.invoke_tool(
                "standardize_document_citations",
                {
                    "text": text,
                    "targetLanguage": target_language.lower(),
                    "fullStatuteNames": full_statute_names,
                },
            )

            content = result.get("content", [])
            if content and isinstance(content, list):
                text_content = content[0].get("text", "{}")
                data: dict[str, Any] = json.loads(text_content)
                return data
            return dict(result)

        except MCPInvocationError as e:
            logger.error(f"Document citation standardization failed: {e}")
            raise

    async def compare_citation_versions(
        self,
        citation1: str,
        citation2: str,
    ) -> dict[str, Any]:
        """
        Compare two citations to determine if they refer to the same source.

        Args:
            citation1: First citation to compare
            citation2: Second citation to compare

        Returns:
            Dict with comparison results including:
            - same_source: Whether citations refer to same source
            - citation1_normalized: Normalized form of citation1
            - citation2_normalized: Normalized form of citation2
            - differences: List of differences if any
            - similarity_score: 0-100 similarity score

        Raises:
            MCPInvocationError: If comparison fails
        """
        try:
            result = await self.client.invoke_tool(
                "compare_citation_versions",
                {
                    "citation1": citation1,
                    "citation2": citation2,
                },
            )

            content = result.get("content", [])
            if content and isinstance(content, list):
                text_content = content[0].get("text", "{}")
                data: dict[str, Any] = json.loads(text_content)
                return data
            return dict(result)

        except MCPInvocationError as e:
            logger.error(f"Citation comparison failed: {e}")
            raise

    async def __aenter__(self) -> "LegalCitationsAdapter":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()
