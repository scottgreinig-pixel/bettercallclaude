"""
Legal research command for BetterCallClaude v2.0

This module implements the /legal:research command for searching Swiss legal sources
including BGE precedents, federal statutes, and cantonal law.
"""

from typing import Any

from ..mcp.connection_manager import MCPConnectionManager
from .base import BaseCommand, CommandCategory, CommandMetadata


class LegalResearchCommand(BaseCommand):
    """
    Search legal sources for precedents and statutes

    Provides unified search across:
    - BGE (Bundesgerichtsentscheide) - Federal Supreme Court decisions
    - Federal statutes (SR - Systematische Rechtssammlung)
    - Cantonal law and regulations
    - Lower court decisions

    Example:
        /legal:research "liability for defective products"
        /legal:research "BGE 147 V 321" --jurisdiction=federal
        /legal:research "rental law" --jurisdiction=ZH --date-from=2020-01-01
    """

    def __init__(self) -> None:
        """Initialize legal research command with metadata and arguments"""
        metadata = CommandMetadata(
            name="legal:research",
            category=CommandCategory.RESEARCH,
            description="Search Swiss legal sources for precedents and statutes",
            help_text=(
                "/legal:research <query> [--jurisdiction=<jur>] "
                "[--date-from=<YYYY-MM-DD>] [--date-to=<YYYY-MM-DD>] "
                "[--limit=<n>]"
            ),
            auto_personas=["legal_researcher", "swiss_law_expert"],
            mcp_servers=["bge_search", "entscheidsuche", "cantonal_courts"],
            requires_auth=False,
        )
        super().__init__(metadata)

        # Define command arguments
        self.add_argument(
            name="query",
            arg_type=str,
            required=True,
            help_text="Search query (legal topic, citation, or keywords)",
        )

        self.add_argument(
            name="jurisdiction",
            arg_type=str,
            required=False,
            default="all",
            help_text=(
                "Jurisdiction filter: 'federal', 'all', or canton code " "(e.g., 'ZH', 'BE', 'GE')"
            ),
        )

        self.add_argument(
            name="date_from",
            arg_type=str,
            required=False,
            default=None,
            help_text="Start date filter (YYYY-MM-DD format)",
        )

        self.add_argument(
            name="date_to",
            arg_type=str,
            required=False,
            default=None,
            help_text="End date filter (YYYY-MM-DD format)",
        )

        self.add_argument(
            name="limit",
            arg_type=int,
            required=False,
            default=10,
            help_text="Maximum number of results to return (default: 10)",
        )

    async def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Execute legal research search using MCP servers

        Args:
            args: Validated command arguments containing:
                - query: Search query string
                - jurisdiction: Jurisdiction filter (optional)
                - date_from: Start date filter (optional)
                - date_to: End date filter (optional)
                - limit: Result limit (optional)

        Returns:
            Dict containing:
                - success: bool
                - results: List of search results
                - sources: List of sources searched
                - metadata: Search metadata (query, filters, count)
        """
        import time

        start_time = time.time()

        query = args.get("query")
        jurisdiction = args.get("jurisdiction", "all")
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        limit = args.get("limit", 10)

        # Initialize connection manager
        conn_manager = MCPConnectionManager()

        # Register MCP servers
        conn_manager.register_server(
            server_id="bge_search",
            name="BGE Search",
            description="Federal Supreme Court decisions",
        )
        conn_manager.register_server(
            server_id="entscheidsuche",
            name="Entscheidsuche",
            description="Swiss court decision search",
        )

        all_results = []
        sources_used = []
        total_results = 0

        try:
            # Search BGE if federal jurisdiction
            if jurisdiction in ["all", "federal"]:
                try:
                    bge_response = await conn_manager.execute(
                        server_id="bge_search",
                        method="search",
                        params={
                            "query": query,
                            "date_from": date_from,
                            "date_to": date_to,
                            "limit": limit,
                        },
                    )

                    if bge_response.get("success"):
                        bge_decisions = bge_response.get("result", {}).get("decisions", [])
                        for decision in bge_decisions:
                            all_results.append(
                                {
                                    "citation": decision.get("citation"),
                                    "title": decision.get("title"),
                                    "court": "Bundesgericht (Federal Supreme Court)",
                                    "date": decision.get("date"),
                                    "summary": decision.get("summary"),
                                    "language": decision.get("language"),
                                    "source": "bge_search",
                                }
                            )
                        sources_used.append("bge_search")
                        total_results += len(bge_decisions)

                except Exception as e:
                    sources_used.append(f"bge_search (error: {str(e)})")

            # Search Entscheidsuche for cantonal/district courts
            if jurisdiction in ["all", "cantonal", "district"]:
                try:
                    court_level = None
                    if jurisdiction == "cantonal":
                        court_level = "cantonal"
                    elif jurisdiction == "district":
                        court_level = "district"

                    entscheid_response = await conn_manager.execute(
                        server_id="entscheidsuche",
                        method="search",
                        params={
                            "query": query,
                            "court_level": court_level,
                            "date_from": date_from,
                            "date_to": date_to,
                            "limit": limit,
                        },
                    )

                    if entscheid_response.get("success"):
                        decisions = entscheid_response.get("result", {}).get("decisions", [])
                        for decision in decisions:
                            all_results.append(
                                {
                                    "decision_id": decision.get("decision_id"),
                                    "title": decision.get("title"),
                                    "court": decision.get("court_name"),
                                    "date": decision.get("date"),
                                    "summary": decision.get("summary"),
                                    "source": "entscheidsuche",
                                }
                            )
                        sources_used.append("entscheidsuche")
                        total_results += len(decisions)

                except Exception as e:
                    sources_used.append(f"entscheidsuche (error: {str(e)})")

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "results": all_results[:limit],  # Limit total results
                "sources": sources_used,
                "metadata": {
                    "query": query,
                    "jurisdiction": jurisdiction,
                    "date_from": date_from,
                    "date_to": date_to,
                    "limit": limit,
                    "total_results": total_results,
                    "execution_time_ms": round(execution_time_ms, 2),
                },
            }

        finally:
            # Clean up connection manager
            await conn_manager.shutdown()
