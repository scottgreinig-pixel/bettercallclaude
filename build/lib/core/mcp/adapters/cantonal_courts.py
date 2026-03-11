"""
Cantonal Courts MCP Adapter

Provides high-level interface to Swiss cantonal court systems (26 cantons)
through MCP server integration, handling cantonal variations and multi-lingual support.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..protocol import MCPClient, MCPInvocationError

logger = logging.getLogger(__name__)


# Swiss canton codes
SWISS_CANTONS = [
    "AG",
    "AI",
    "AR",
    "BE",
    "BL",
    "BS",
    "FR",
    "GE",
    "GL",
    "GR",
    "JU",
    "LU",
    "NE",
    "NW",
    "OW",
    "SG",
    "SH",
    "SO",
    "SZ",
    "TG",
    "TI",
    "UR",
    "VD",
    "VS",
    "ZG",
    "ZH",
]


@dataclass
class CantonalCourt:
    """Information about a cantonal court"""

    canton: str  # 2-letter canton code
    name: str  # Court name
    court_type: str  # supreme, appellate, district, etc.
    languages: list[str]  # Official languages for this court
    website_url: str | None = None


@dataclass
class CantonalDecision:
    """Represents a cantonal court decision"""

    decision_id: str
    canton: str  # Canton code
    court: CantonalCourt
    title: str
    date: datetime
    language: str
    summary: str
    legal_areas: list[str]
    case_number: str  # Canton-specific case numbering
    parties: dict[str, str] | None = None  # Plaintiff, defendant info
    full_text_url: str | None = None


@dataclass
class CantonalSearchResult:
    """Results from cantonal courts search"""

    query: str
    cantons_searched: list[str]
    total_results: int
    decisions: list[CantonalDecision]
    by_canton: dict[str, int]  # Result count per canton
    search_time_ms: float
    metadata: dict[str, Any]


class CantonalCourtsAdapter:
    """
    High-level adapter for Swiss cantonal courts

    Provides unified interface to search decisions across 26 cantonal
    court systems, handling cantonal variations and language differences.

    Example:
        adapter = CantonalCourtsAdapter(
            command=["node", "mcp-servers/cantonal-courts/dist/index.js"]
        )

        async with adapter:
            # Search specific canton
            zh_results = await adapter.search(
                query="Mietrecht",
                cantons=["ZH"],
                language="DE"
            )

            # Search across multiple cantons
            all_results = await adapter.search(
                query="droit du travail",
                cantons=["GE", "VD", "NE"],
                language="FR"
            )

            # Get available courts
            courts = await adapter.list_courts(canton="BE")
    """

    def __init__(
        self,
        command: list[str],
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize Cantonal Courts adapter

        Args:
            command: Command to start Cantonal Courts MCP server
            env: Optional environment variables
            timeout: Request timeout in seconds
        """
        self.client = MCPClient(
            command=command, server_id="cantonal_courts", env=env, timeout=timeout
        )

    async def connect(self) -> None:
        """Connect to Cantonal Courts MCP server"""
        await self.client.connect()
        await self.client.initialize()
        logger.info("Cantonal Courts adapter connected and initialized")

    async def disconnect(self) -> None:
        """Disconnect from Cantonal Courts MCP server"""
        await self.client.disconnect()

    async def search(
        self,
        query: str,
        cantons: list[str] | None = None,
        court_type: str | None = None,
        language: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        legal_areas: list[str] | None = None,
        limit: int = 10,
    ) -> CantonalSearchResult:
        """
        Search cantonal court decisions

        Args:
            query: Search query (supports natural language)
            cantons: Filter by cantons (2-letter codes: ZH, BE, etc.)
                    If None, searches all cantons
            court_type: Filter by court type (supreme, appellate, district)
            language: Filter by language (DE, FR, IT, RM)
            date_from: Filter by date from (YYYY-MM-DD)
            date_to: Filter by date to (YYYY-MM-DD)
            legal_areas: Filter by legal areas
            limit: Maximum results to return per canton

        Returns:
            CantonalSearchResult with matching decisions

        Raises:
            MCPInvocationError: If search fails
        """
        # Validate cantons
        if cantons:
            invalid = [c for c in cantons if c.upper() not in SWISS_CANTONS]
            if invalid:
                raise ValueError(f"Invalid canton codes: {invalid}")
            cantons = [c.upper() for c in cantons]
        else:
            cantons = SWISS_CANTONS

        # Build search parameters
        params = {
            "query": query,
            "cantons": cantons,
            "limit": limit,
        }

        if court_type:
            params["courtType"] = court_type
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
            result = await self.client.invoke_tool("search_cantonal_decisions", params)

            # Parse results
            decisions = []
            for item in result.get("decisions", []):
                decision = self._parse_decision(item)
                decisions.append(decision)

            return CantonalSearchResult(
                query=query,
                cantons_searched=cantons,
                total_results=result.get("totalResults", len(decisions)),
                decisions=decisions,
                by_canton=result.get("byCanton", {}),
                search_time_ms=result.get("searchTimeMs", 0.0),
                metadata=result.get("metadata", {}),
            )

        except MCPInvocationError as e:
            logger.error(f"Cantonal courts search failed: {e}")
            raise

    async def get_decision(self, decision_id: str, canton: str) -> CantonalDecision | None:
        """
        Retrieve specific cantonal decision

        Args:
            decision_id: Decision identifier
            canton: Canton code (2-letter)

        Returns:
            CantonalDecision or None if not found

        Raises:
            MCPInvocationError: If retrieval fails
        """
        try:
            result = await self.client.invoke_tool(
                "get_cantonal_decision",
                {"decisionId": decision_id, "canton": canton.upper()},
            )

            if result.get("found"):
                return self._parse_decision(result.get("decision", {}))
            return None

        except MCPInvocationError as e:
            logger.error(f"Cantonal decision retrieval failed: {e}")
            raise

    async def list_courts(self, canton: str | None = None) -> list[CantonalCourt]:
        """
        List available cantonal courts

        Args:
            canton: Optional canton filter (2-letter code)
                   If None, lists courts for all cantons

        Returns:
            List of CantonalCourt objects

        Raises:
            MCPInvocationError: If listing fails
        """
        params = {}
        if canton:
            if canton.upper() not in SWISS_CANTONS:
                raise ValueError(f"Invalid canton code: {canton}")
            params["canton"] = canton.upper()

        try:
            result = await self.client.invoke_tool("list_cantonal_courts", params)

            courts = []
            for item in result.get("courts", []):
                court = CantonalCourt(
                    canton=item.get("canton", ""),
                    name=item.get("name", ""),
                    court_type=item.get("courtType", ""),
                    languages=item.get("languages", []),
                    website_url=item.get("websiteUrl"),
                )
                courts.append(court)

            return courts

        except MCPInvocationError as e:
            logger.error(f"Court listing failed: {e}")
            raise

    def _parse_decision(self, data: dict[str, Any]) -> CantonalDecision:
        """Parse decision data from MCP server response"""
        # Parse date
        date_str = data.get("date", "")
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            date = datetime.now()  # Fallback

        # Parse court info
        court_data = data.get("court", {})
        court = CantonalCourt(
            canton=court_data.get("canton", data.get("canton", "")),
            name=court_data.get("name", ""),
            court_type=court_data.get("courtType", ""),
            languages=court_data.get("languages", []),
            website_url=court_data.get("websiteUrl"),
        )

        return CantonalDecision(
            decision_id=data.get("decisionId", ""),
            canton=data.get("canton", ""),
            court=court,
            title=data.get("title", ""),
            date=date,
            language=data.get("language", "DE"),
            summary=data.get("summary", ""),
            legal_areas=data.get("legalAreas", []),
            case_number=data.get("caseNumber", ""),
            parties=data.get("parties"),
            full_text_url=data.get("fullTextUrl"),
        )

    async def __aenter__(self) -> "CantonalCourtsAdapter":
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.disconnect()
