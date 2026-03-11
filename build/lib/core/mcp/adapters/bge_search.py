"""
BGE Search MCP Adapter

Provides high-level interface to BGE (Bundesgerichtsentscheide) Federal
Supreme Court decisions through MCP server integration.

BGE Citation Format: BGE [Volume] [Chamber] [Page]
Example: BGE 147 V 321
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..protocol import MCPClient, MCPInvocationError

logger = logging.getLogger(__name__)


@dataclass
class BGEDecision:
    """Represents a BGE Federal Supreme Court decision"""

    citation: str  # e.g., "BGE 147 V 321"
    volume: str  # Volume number
    chamber: str  # Chamber (I-V for main chambers)
    page: str  # Starting page
    title: str  # Decision title
    date: datetime  # Decision date
    language: str  # DE, FR, or IT
    summary: str  # Decision summary
    legal_areas: list[str]  # Legal area classifications
    full_text_url: str | None = None  # Link to full decision text


@dataclass
class BGESearchResult:
    """Results from BGE search query"""

    query: str
    total_results: int
    decisions: list[BGEDecision]
    search_time_ms: float
    metadata: dict[str, Any]


class BGESearchAdapter:
    """
    High-level adapter for BGE Federal Supreme Court search

    Provides Swiss-legal-domain-specific interface to BGE search MCP server,
    handling citation parsing, multi-lingual support, and result formatting.

    Example:
        adapter = BGESearchAdapter(
            command=["node", "mcp-servers/bge-search/dist/index.js"]
        )

        async with adapter:
            results = await adapter.search(
                query="sozialversicherung invalidität",
                language="DE",
                limit=10
            )

            for decision in results.decisions:
                print(f"{decision.citation}: {decision.title}")
    """

    def __init__(
        self,
        command: list[str],
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize BGE search adapter

        Args:
            command: Command to start BGE search MCP server
            env: Optional environment variables
            timeout: Request timeout in seconds
        """
        self.client = MCPClient(command=command, server_id="bge_search", env=env, timeout=timeout)

    async def connect(self) -> None:
        """Connect to BGE search MCP server"""
        await self.client.connect()
        await self.client.initialize()
        logger.info("BGE Search adapter connected and initialized")

    async def disconnect(self) -> None:
        """Disconnect from BGE search MCP server"""
        await self.client.disconnect()

    async def search(
        self,
        query: str,
        language: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        chambers: list[str] | None = None,
        legal_areas: list[str] | None = None,
        limit: int = 10,
    ) -> BGESearchResult:
        """
        Search BGE Federal Supreme Court decisions

        Args:
            query: Search query (supports natural language)
            language: Filter by language (DE, FR, IT)
            date_from: Filter by date from (YYYY-MM-DD)
            date_to: Filter by date to (YYYY-MM-DD)
            chambers: Filter by chambers (I, II, III, IV, V)
            legal_areas: Filter by legal areas
            limit: Maximum results to return

        Returns:
            BGESearchResult with matching decisions

        Raises:
            MCPInvocationError: If search fails
        """
        # Build search parameters
        params = {"query": query, "limit": limit}

        if language:
            params["language"] = language.upper()
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if chambers:
            params["chambers"] = chambers
        if legal_areas:
            params["legalAreas"] = legal_areas

        # Invoke search tool
        try:
            result = await self.client.invoke_tool("search_bge", params)

            # Parse results
            decisions = []
            for item in result.get("decisions", []):
                decision = self._parse_decision(item)
                decisions.append(decision)

            return BGESearchResult(
                query=query,
                total_results=result.get("totalResults", len(decisions)),
                decisions=decisions,
                search_time_ms=result.get("searchTimeMs", 0.0),
                metadata=result.get("metadata", {}),
            )

        except MCPInvocationError as e:
            logger.error(f"BGE search failed: {e}")
            raise

    async def get_decision(self, citation: str) -> BGEDecision | None:
        """
        Retrieve specific BGE decision by citation

        Args:
            citation: BGE citation (e.g., "BGE 147 V 321")

        Returns:
            BGEDecision or None if not found

        Raises:
            MCPInvocationError: If retrieval fails
        """
        try:
            result = await self.client.invoke_tool("get_bge_decision", {"citation": citation})

            if result.get("found"):
                return self._parse_decision(result.get("decision", {}))
            return None

        except MCPInvocationError as e:
            logger.error(f"BGE decision retrieval failed: {e}")
            raise

    async def validate_citation(self, citation: str) -> dict[str, Any]:
        """
        Validate BGE citation format

        Args:
            citation: Citation to validate (e.g., "BGE 147 V 321")

        Returns:
            Dict with validation result and parsed components

        Example:
            {
                "valid": True,
                "volume": "147",
                "chamber": "V",
                "page": "321",
                "normalized": "BGE 147 V 321"
            }
        """
        try:
            result = await self.client.invoke_tool("validate_bge_citation", {"citation": citation})
            return result

        except MCPInvocationError as e:
            logger.error(f"Citation validation failed: {e}")
            return {"valid": False, "error": str(e)}

    def _parse_decision(self, data: dict[str, Any]) -> BGEDecision:
        """Parse decision data from MCP server response"""
        # Parse date
        date_str = data.get("date", "")
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            date = datetime.now()  # Fallback

        return BGEDecision(
            citation=data.get("citation", ""),
            volume=data.get("volume", ""),
            chamber=data.get("chamber", ""),
            page=data.get("page", ""),
            title=data.get("title", ""),
            date=date,
            language=data.get("language", "DE"),
            summary=data.get("summary", ""),
            legal_areas=data.get("legalAreas", []),
            full_text_url=data.get("fullTextUrl"),
        )

    async def __aenter__(self) -> "BGESearchAdapter":
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.disconnect()
