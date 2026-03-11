"""
Entscheidsuche MCP Adapter

Provides high-level interface to Swiss court decision search across
federal and cantonal courts through MCP server integration.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..protocol import MCPClient, MCPInvocationError

logger = logging.getLogger(__name__)


@dataclass
class CourtDecision:
    """Represents a Swiss court decision from any court level"""

    decision_id: str  # Unique decision identifier
    court_name: str  # Court name
    court_level: str  # federal, cantonal, district, municipal
    canton: str | None  # Canton code (for cantonal/lower courts)
    title: str  # Decision title
    date: datetime  # Decision date
    language: str  # DE, FR, IT, or RM
    summary: str  # Decision summary
    legal_areas: list[str]  # Legal area classifications
    reference_number: str  # Court's own reference number
    related_decisions: list[str] = field(default_factory=list)  # Related decision IDs
    full_text_url: str | None = None  # Link to full text


@dataclass
class EntscheidausucheSearchResult:
    """Results from Entscheidsuche query"""

    query: str
    total_results: int
    decisions: list[CourtDecision]
    facets: dict[str, list[dict[str, Any]]]  # Search facets (courts, areas, dates)
    search_time_ms: float
    metadata: dict[str, Any]


class EntscheidausucheAdapter:
    """
    High-level adapter for Swiss court decision search

    Provides unified interface to search decisions across federal and
    cantonal courts, handling multi-lingual queries and court hierarchy.

    Example:
        adapter = EntscheidausucheAdapter(
            command=["node", "mcp-servers/entscheidsuche/dist/index.js"]
        )

        async with adapter:
            results = await adapter.search(
                query="arbeitsrecht kündigung",
                court_level="cantonal",
                canton="ZH",
                language="DE"
            )

            for decision in results.decisions:
                print(f"{decision.court_name}: {decision.title}")
    """

    def __init__(
        self,
        command: list[str],
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize Entscheidsuche adapter

        Args:
            command: Command to start Entscheidsuche MCP server
            env: Optional environment variables
            timeout: Request timeout in seconds
        """
        self.client = MCPClient(
            command=command, server_id="entscheidsuche", env=env, timeout=timeout
        )

    async def connect(self) -> None:
        """Connect to Entscheidsuche MCP server"""
        await self.client.connect()
        await self.client.initialize()
        logger.info("Entscheidsuche adapter connected and initialized")

    async def disconnect(self) -> None:
        """Disconnect from Entscheidsuche MCP server"""
        await self.client.disconnect()

    async def search(
        self,
        query: str,
        court_level: str | None = None,
        canton: str | None = None,
        language: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        legal_areas: list[str] | None = None,
        limit: int = 10,
    ) -> EntscheidausucheSearchResult:
        """
        Search Swiss court decisions

        Args:
            query: Search query (supports natural language)
            court_level: Filter by court level (federal, cantonal, district, municipal)
            canton: Filter by canton (2-letter code: ZH, BE, GE, etc.)
            language: Filter by language (DE, FR, IT, RM)
            date_from: Filter by date from (YYYY-MM-DD)
            date_to: Filter by date to (YYYY-MM-DD)
            legal_areas: Filter by legal areas
            limit: Maximum results to return

        Returns:
            EntscheidausucheSearchResult with matching decisions

        Raises:
            MCPInvocationError: If search fails
        """
        # Build search parameters
        params = {"query": query, "limit": limit}

        if court_level:
            params["courtLevel"] = court_level
        if canton:
            params["canton"] = canton.upper()
        if language:
            params["language"] = language.upper()
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if legal_areas:
            params["legalAreas"] = legal_areas

        # Invoke search tool
        try:
            result = await self.client.invoke_tool("search_decisions", params)

            # Parse results
            decisions = []
            for item in result.get("decisions", []):
                decision = self._parse_decision(item)
                decisions.append(decision)

            return EntscheidausucheSearchResult(
                query=query,
                total_results=result.get("totalResults", len(decisions)),
                decisions=decisions,
                facets=result.get("facets", {}),
                search_time_ms=result.get("searchTimeMs", 0.0),
                metadata=result.get("metadata", {}),
            )

        except MCPInvocationError as e:
            logger.error(f"Entscheidsuche search failed: {e}")
            raise

    async def get_decision(self, decision_id: str) -> CourtDecision | None:
        """
        Retrieve specific decision by ID

        Args:
            decision_id: Decision identifier

        Returns:
            CourtDecision or None if not found

        Raises:
            MCPInvocationError: If retrieval fails
        """
        try:
            result = await self.client.invoke_tool("get_decision", {"decisionId": decision_id})

            if result.get("found"):
                return self._parse_decision(result.get("decision", {}))
            return None

        except MCPInvocationError as e:
            logger.error(f"Decision retrieval failed: {e}")
            raise

    async def get_related_decisions(self, decision_id: str, limit: int = 5) -> list[CourtDecision]:
        """
        Find related decisions (cited, citing, similar)

        Args:
            decision_id: Decision identifier
            limit: Maximum related decisions to return

        Returns:
            List of related CourtDecision objects

        Raises:
            MCPInvocationError: If retrieval fails
        """
        try:
            result = await self.client.invoke_tool(
                "get_related_decisions", {"decisionId": decision_id, "limit": limit}
            )

            decisions = []
            for item in result.get("relatedDecisions", []):
                decision = self._parse_decision(item)
                decisions.append(decision)

            return decisions

        except MCPInvocationError as e:
            logger.error(f"Related decisions retrieval failed: {e}")
            raise

    def _parse_decision(self, data: dict[str, Any]) -> CourtDecision:
        """Parse decision data from MCP server response"""
        # Parse date
        date_str = data.get("date", "")
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            date = datetime.now()  # Fallback

        return CourtDecision(
            decision_id=data.get("decisionId", ""),
            court_name=data.get("courtName", ""),
            court_level=data.get("courtLevel", ""),
            canton=data.get("canton"),
            title=data.get("title", ""),
            date=date,
            language=data.get("language", "DE"),
            summary=data.get("summary", ""),
            legal_areas=data.get("legalAreas", []),
            reference_number=data.get("referenceNumber", ""),
            related_decisions=data.get("relatedDecisions", []),
            full_text_url=data.get("fullTextUrl"),
        )

    async def analyze_precedent_success_rate(
        self,
        legal_area: str,
        claim_type: str | None = None,
        court_level: str | None = None,
        canton: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze precedent success rates for a legal area

        Args:
            legal_area: Legal area to analyze (e.g., "arbeitsrecht", "mietrecht")
            claim_type: Type of legal claim (optional)
            court_level: Court level filter (federal, cantonal, all)
            canton: Canton filter for cantonal decisions

        Returns:
            Dict with success rate analysis including:
            - overall_success_rate: Overall success percentage
            - sample_size: Number of decisions analyzed
            - breakdown_by_court_level: Success rates by court level
            - breakdown_by_canton: Success rates by canton (if cantonal data)
            - breakdown_by_year: Success rates by year
            - key_factors: Factors influencing success
            - recommendations: Strategic recommendations

        Raises:
            MCPInvocationError: If analysis fails
        """
        params: dict[str, Any] = {"legalArea": legal_area}

        if claim_type:
            params["claimType"] = claim_type
        if court_level:
            params["courtLevel"] = court_level
        if canton:
            params["canton"] = canton.upper()

        try:
            result = await self.client.invoke_tool("analyze_precedent_success_rate", params)
            return result

        except MCPInvocationError as e:
            logger.error(f"Precedent success rate analysis failed: {e}")
            raise

    async def find_similar_cases(
        self,
        decision_id: str | None = None,
        fact_pattern: str | None = None,
        legal_area: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Find similar cases based on decision ID or fact pattern

        Args:
            decision_id: Base decision ID to find similar cases for
            fact_pattern: Text description of facts to match
            legal_area: Filter by legal area
            limit: Maximum number of similar cases to return

        Returns:
            Dict with similar cases including:
            - similar_cases: List of similar decisions with similarity scores
            - total_found: Total number of similar cases found
            - base_decision: The base decision (if decision_id provided)

            Each similar case includes:
            - decision: CourtDecision data
            - similarity_score: 0-100 score
            - matching_factors: What makes it similar

        Raises:
            MCPInvocationError: If search fails
            ValueError: If neither decision_id nor fact_pattern provided
        """
        if not decision_id and not fact_pattern:
            raise ValueError("Either decision_id or fact_pattern must be provided")

        params: dict[str, Any] = {"limit": limit}

        if decision_id:
            params["decisionId"] = decision_id
        if fact_pattern:
            params["factPattern"] = fact_pattern
        if legal_area:
            params["legalArea"] = legal_area

        try:
            result = await self.client.invoke_tool("find_similar_cases", params)
            return result

        except MCPInvocationError as e:
            logger.error(f"Similar case search failed: {e}")
            raise

    async def get_legal_provision_interpretation(
        self,
        statute: str,
        article: str,
        paragraph: str | None = None,
        language: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Get court interpretations of a statutory provision

        Args:
            statute: Statute abbreviation (ZGB, OR, StGB, etc.)
            article: Article number
            paragraph: Paragraph/Absatz number (optional)
            language: Filter by language (DE, FR, IT)
            limit: Maximum interpretations to return

        Returns:
            Dict with interpretation data including:
            - provision: The statutory provision reference
            - interpretations: List of court interpretations
            - total_found: Total interpretations found

            Each interpretation includes:
            - decision_id: Court decision ID
            - court_name: Name of the court
            - date: Decision date
            - interpretation_text: Relevant text from decision
            - context: Surrounding context
            - binding_level: How binding the interpretation is

        Raises:
            MCPInvocationError: If retrieval fails
        """
        params: dict[str, Any] = {
            "statute": statute.upper(),
            "article": article,
            "limit": limit,
        }

        if paragraph:
            params["paragraph"] = paragraph
        if language:
            params["language"] = language.upper()

        try:
            result = await self.client.invoke_tool("get_legal_provision_interpretation", params)
            return result

        except MCPInvocationError as e:
            logger.error(f"Legal provision interpretation retrieval failed: {e}")
            raise

    async def __aenter__(self) -> "EntscheidausucheAdapter":
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.disconnect()
