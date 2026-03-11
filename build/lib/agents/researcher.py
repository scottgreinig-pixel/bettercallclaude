"""
BetterCallClaude Researcher Agent

The foundational legal research agent that enables the 80% time savings target.
Performs deep, multi-source legal research with automatic citation verification.

Workflow:
1. UNDERSTAND - Parse question, identify legal issues
2. PLAN - Determine search strategy
3. SEARCH - Execute parallel searches across sources
4. VERIFY - Verify citations via sub-agent
5. SYNTHESIZE - Analyze findings, identify patterns
6. DELIVER - Generate research memo
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .base import (
    ActionType,
    AgentBase,
    AgentOutcome,
    AgentResult,
    AutonomyMode,
    CaseContext,
)

# =============================================================================
# Research-Specific Data Classes
# =============================================================================


class LegalDomain(Enum):
    """Swiss legal domains for classification."""

    CONTRACT = "contract"  # Vertragsrecht (OR)
    TORT = "tort"  # Haftpflichtrecht
    PROPERTY = "property"  # Sachenrecht (ZGB)
    FAMILY = "family"  # Familienrecht
    SUCCESSION = "succession"  # Erbrecht
    CORPORATE = "corporate"  # Gesellschaftsrecht
    EMPLOYMENT = "employment"  # Arbeitsrecht
    CRIMINAL = "criminal"  # Strafrecht (StGB)
    ADMINISTRATIVE = "administrative"  # Verwaltungsrecht
    PROCEDURAL = "procedural"  # Verfahrensrecht (ZPO, StPO)
    DEBT_COLLECTION = "debt_collection"  # SchKG
    INTELLECTUAL_PROPERTY = "ip"  # Immaterialgüterrecht
    OTHER = "other"


class ResearchDepth(Enum):
    """Research depth levels."""

    QUICK = "quick"  # 2 min, 10 sources
    STANDARD = "standard"  # 5 min, 30 sources
    DEEP = "deep"  # 10 min, 50+ sources


@dataclass
class ResearchParameters:
    """Extracted parameters from research question."""

    original_question: str
    legal_domains: list[LegalDomain]
    key_terms: list[str]
    concepts: list[str]
    jurisdiction_federal: bool
    jurisdiction_cantons: list[str]
    time_range_from: datetime | None = None
    time_range_to: datetime | None = None
    languages: list[str] = field(default_factory=lambda: ["DE"])
    statute_references: list[str] = field(default_factory=list)


@dataclass
class SearchSource:
    """Configuration for a search source."""

    name: str
    priority: int
    expected_volume: int
    mcp_server: str
    search_method: str


@dataclass
class SearchQuery:
    """A single search query for a source."""

    source: str
    query: str
    filters: dict[str, Any]
    language: str
    max_results: int


@dataclass
class SearchStrategy:
    """Complete search strategy."""

    sources: list[SearchSource]
    queries: list[SearchQuery]
    relevance_threshold: float
    max_total_results: int
    parallel_limit: int


@dataclass
class RawResult:
    """A single search result."""

    id: str
    title: str
    citation: str
    date: datetime | None
    court: str
    summary: str
    relevance_score: float
    source: str
    full_text_url: str | None = None
    language: str = "DE"


@dataclass
class SearchResults:
    """Aggregated search results."""

    results: list[RawResult]
    by_source: dict[str, list[RawResult]]
    total_found: int
    deduplicated_count: int
    processing_time_ms: int


@dataclass
class VerifiedCitation:
    """A verified citation."""

    citation: str
    is_valid: bool
    is_current: bool
    formatted: str
    court: str
    date: datetime | None
    issues: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    """Citation verification report."""

    verified: list[VerifiedCitation]
    outdated: list[VerifiedCitation]
    errors: list[dict[str, str]]
    overall_accuracy: float


@dataclass
class Finding:
    """A research finding."""

    issue: str
    conclusion: str
    supporting_citations: list[str]
    confidence: float
    conflicts: list[str] = field(default_factory=list)


@dataclass
class Synthesis:
    """Research synthesis."""

    key_findings: list[Finding]
    precedent_chain: list[str]
    conflicts: list[dict[str, Any]]
    gaps: list[str]
    recommendations: list[str]


@dataclass
class ResearchMemo:
    """Final research deliverable."""

    title: str
    executive_summary: str
    methodology: str
    findings: list[Finding]
    citations: list[VerifiedCitation]
    limitations: list[str]
    next_steps: list[str]
    metadata: dict[str, Any]


# =============================================================================
# MCP Client Interface (Abstract)
# =============================================================================


class MCPClient:
    """
    Abstract MCP client for legal research servers.

    In production, this would connect to actual MCP servers.
    For now, provides interface definition and mock responses.
    """

    async def call(self, server: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Call an MCP server method.

        Args:
            server: MCP server name (e.g., "bge-search")
            method: Method to call (e.g., "search")
            params: Parameters for the method

        Returns:
            Response from the MCP server
        """
        # Mock implementation - replace with actual MCP calls
        return await self._mock_response(server, method, params)

    async def _mock_response(
        self, server: str, method: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate mock responses for testing."""
        if server == "bge-search" and method == "search":
            return {
                "results": [
                    {
                        "id": "BGE-142-III-234",
                        "title": "Werkvertrag; Mängelhaftung",
                        "citation": "BGE 142 III 234",
                        "date": "2016-05-15",
                        "court": "Bundesgericht",
                        "summary": "Grundsatzentscheid zur Mängelhaftung im Werkvertrag...",
                        "relevance_score": 0.95,
                        "full_text_url": "https://bger.ch/ext/142-III-234",
                    }
                ],
                "total": 1,
            }
        elif server == "cantonal-courts" and method == "search":
            return {"results": [], "total": 0}
        elif server == "legal-citations" and method == "verify":
            return {
                "verified": True,
                "formatted": params.get("citation", ""),
                "is_current": True,
                "issues": [],
            }
        return {"results": [], "total": 0}


# =============================================================================
# Researcher Agent
# =============================================================================


class ResearcherAgent(AgentBase):
    """
    Legal research agent for Swiss law.

    Performs deep, multi-source research with citation verification.
    Implements the workflow defined in AGENT_RESEARCHER_SPEC.md.
    """

    # Legal term patterns for Swiss law
    SWISS_STATUTES = {
        "OR": "Obligationenrecht",
        "ZGB": "Zivilgesetzbuch",
        "StGB": "Strafgesetzbuch",
        "ZPO": "Zivilprozessordnung",
        "StPO": "Strafprozessordnung",
        "SchKG": "Schuldbetreibungs- und Konkursgesetz",
        "VwVG": "Verwaltungsverfahrensgesetz",
        "BGG": "Bundesgerichtsgesetz",
    }

    SWISS_CANTONS = [
        "ZH",
        "BE",
        "LU",
        "UR",
        "SZ",
        "OW",
        "NW",
        "GL",
        "ZG",
        "FR",
        "SO",
        "BS",
        "BL",
        "SH",
        "AR",
        "AI",
        "SG",
        "GR",
        "AG",
        "TG",
        "TI",
        "VD",
        "VS",
        "NE",
        "GE",
        "JU",
    ]

    DOMAIN_KEYWORDS = {
        LegalDomain.CONTRACT: [
            "Vertrag",
            "Werkvertrag",
            "Kaufvertrag",
            "Miete",
            "Pacht",
            "Mängel",
            "Gewährleistung",
            "Verzug",
            "Schadenersatz",
            "OR",
        ],
        LegalDomain.TORT: [
            "Haftung",
            "Haftpflicht",
            "Schaden",
            "Kausalität",
            "Verschulden",
            "Gefährdungshaftung",
            "unerlaubte Handlung",
        ],
        LegalDomain.EMPLOYMENT: [
            "Arbeit",
            "Kündigung",
            "Arbeitsvertrag",
            "Lohn",
            "Überstunden",
            "Ferienanspruch",
            "Arbeitszeugnis",
        ],
        LegalDomain.CORPORATE: [
            "AG",
            "GmbH",
            "Aktie",
            "Generalversammlung",
            "Verwaltungsrat",
            "Gesellschaft",
            "Kapital",
        ],
        LegalDomain.CRIMINAL: ["Straf", "Betrug", "Diebstahl", "Körperverletzung", "StGB"],
        LegalDomain.DEBT_COLLECTION: [
            "Betreibung",
            "Konkurs",
            "Pfändung",
            "Rechtsvorschlag",
            "SchKG",
        ],
    }

    def __init__(
        self,
        autonomy_mode: AutonomyMode = AutonomyMode.BALANCED,
        case_context: CaseContext | None = None,
        user_id: str = "anonymous",
        firm_id: str = "default",
        mcp_client: MCPClient | None = None,
    ):
        """Initialize researcher agent."""
        super().__init__(autonomy_mode, case_context, user_id, firm_id)
        self.mcp_client = mcp_client or MCPClient()

    @property
    def agent_id(self) -> str:
        return "researcher"

    @property
    def agent_version(self) -> str:
        return "1.0.0"

    async def execute(
        self,
        task: str,
        depth: str = "standard",
        max_sources: int = 50,
        output_format: str = "memo",
        **kwargs: Any,
    ) -> AgentResult[ResearchMemo]:
        """
        Execute legal research workflow.

        Args:
            task: Research question in natural language
            depth: "quick" | "standard" | "deep"
            max_sources: Maximum number of sources to search
            output_format: "memo" | "bullets" | "json"

        Returns:
            AgentResult containing ResearchMemo
        """
        self._start_time = datetime.utcnow()
        self._reset_state()

        research_depth = ResearchDepth(depth)
        self.update_state("depth", depth)
        self.update_state("max_sources", max_sources)

        self.create_checkpoint("auto", "Research started")

        try:
            # Step 1: UNDERSTAND
            params = await self._understand(task)
            self.create_checkpoint("auto", "Parameters extracted")

            # Step 2: PLAN
            strategy = await self._plan(params, research_depth, max_sources)

            if self.autonomy_mode == AutonomyMode.CAUTIOUS:
                await self._confirm_strategy(strategy)
            elif self.autonomy_mode == AutonomyMode.BALANCED:
                await self._show_strategy_summary(strategy)

            # Step 3: SEARCH
            results = await self._search(strategy)
            self.create_checkpoint("auto", f"Search completed: {len(results.results)} results")

            # Step 4: VERIFY
            verification = await self._verify(results)

            if self.autonomy_mode in [AutonomyMode.CAUTIOUS, AutonomyMode.BALANCED]:
                await self._report_verification(verification)

            # Step 5: SYNTHESIZE
            synthesis = await self._synthesize(results, verification, params)
            self.create_checkpoint("auto", "Synthesis completed")

            # Step 6: DELIVER
            memo = await self._deliver(synthesis, params, results, verification)

            return self._create_success_result(memo)

        except Exception as e:
            self._handle_error(e)
            return self._create_failure_result(e)

    def _reset_state(self) -> None:
        """Reset execution state for new run."""
        self._actions = []
        self._checkpoints = []
        self._sources_accessed = []
        self._documents_read = []
        self._documents_written = []
        self._errors = []
        self._current_state = {}

    # -------------------------------------------------------------------------
    # Step 1: UNDERSTAND
    # -------------------------------------------------------------------------

    async def _understand(self, question: str) -> ResearchParameters:
        """
        Parse research question and extract parameters.

        Identifies:
        - Legal domains (contract, tort, etc.)
        - Key terms and concepts
        - Jurisdiction requirements
        - Time constraints
        - Language requirements
        """
        start = datetime.utcnow()

        # Detect legal domains
        domains = self._detect_domains(question)

        # Extract key terms
        key_terms = self._extract_key_terms(question)

        # Extract statute references (e.g., "Art. 368 OR")
        statute_refs = self._extract_statute_references(question)

        # Detect jurisdiction
        federal, cantons = self._detect_jurisdiction(question)

        # Detect languages
        languages = self._detect_languages(question)

        # Extract concepts
        concepts = self._extract_concepts(question, domains)

        params = ResearchParameters(
            original_question=question,
            legal_domains=domains,
            key_terms=key_terms,
            concepts=concepts,
            jurisdiction_federal=federal,
            jurisdiction_cantons=cantons,
            languages=languages,
            statute_references=statute_refs,
        )

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        self._record_action(
            ActionType.ANALYZE,
            "Parsed research question",
            inputs={"question": question},
            outputs={
                "domains": [d.value for d in domains],
                "key_terms": key_terms,
                "cantons": cantons,
            },
            duration_ms=duration_ms,
        )

        self.update_state("parameters", params)
        return params

    def _detect_domains(self, question: str) -> list[LegalDomain]:
        """Detect legal domains from question text."""
        question_lower = question.lower()
        detected = []

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    if domain not in detected:
                        detected.append(domain)
                    break

        if not detected:
            detected.append(LegalDomain.OTHER)

        return detected

    def _extract_key_terms(self, question: str) -> list[str]:
        """Extract key legal terms from question."""
        # Remove common words
        stopwords = {
            "der",
            "die",
            "das",
            "und",
            "oder",
            "ist",
            "sind",
            "was",
            "wie",
            "wer",
            "welche",
            "welcher",
            "nach",
            "bei",
            "für",
            "the",
            "and",
            "or",
            "is",
            "are",
            "what",
            "how",
            "which",
        }

        words = re.findall(r"\b\w+\b", question)
        terms = []

        for word in words:
            if len(word) > 3 and word.lower() not in stopwords:
                # Capitalize if it's a German noun (simplified heuristic)
                if word[0].isupper() or word.isupper():
                    terms.append(word)

        # Also extract quoted phrases
        quoted = re.findall(r'"([^"]+)"', question)
        terms.extend(quoted)

        return list(set(terms))[:20]  # Limit to 20 terms

    def _extract_statute_references(self, question: str) -> list[str]:
        """Extract statute references like 'Art. 368 OR'."""
        patterns = [
            r"Art\.?\s*\d+(?:\s*(?:Abs|lit|Ziff)\.?\s*\d+)*\s*(?:OR|ZGB|StGB|ZPO|StPO|SchKG|BGG)",
            r"§\s*\d+\s*[A-Za-z]+",
        ]

        refs = []
        for pattern in patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            refs.extend(matches)

        return list(set(refs))

    def _detect_jurisdiction(self, question: str) -> tuple[bool, list[str]]:
        """Detect federal and cantonal jurisdiction from question."""
        question_upper = question.upper()

        # Check for cantonal references
        cantons = []
        for canton in self.SWISS_CANTONS:
            if canton in question_upper or f"KANTON {canton}" in question_upper:
                cantons.append(canton)

        # Check for explicit cantonal keywords
        cantonal_keywords = ["kantonal", "cantonal", "Obergericht", "Handelsgericht"]
        has_cantonal = any(kw.lower() in question.lower() for kw in cantonal_keywords)

        # Check for federal keywords
        federal_keywords = ["BGE", "Bundesgericht", "federal", "eidgenössisch"]
        has_federal = any(kw.lower() in question.lower() for kw in federal_keywords)

        # Default to federal if no specific indication
        federal = has_federal or (not has_cantonal and not cantons)

        return federal, cantons

    def _detect_languages(self, question: str) -> list[str]:
        """Detect language requirements from question."""
        # Simple heuristic based on question content
        german_indicators = ["Vertrag", "Recht", "Gesetz", "Urteil"]
        french_indicators = ["contrat", "droit", "loi", "arrêt"]
        italian_indicators = ["contratto", "diritto", "legge", "sentenza"]
        english_indicators = ["contract", "law", "judgment", "ruling"]

        languages = []

        if any(ind in question for ind in german_indicators):
            languages.append("DE")
        if any(ind in question for ind in french_indicators):
            languages.append("FR")
        if any(ind in question for ind in italian_indicators):
            languages.append("IT")
        if any(ind in question for ind in english_indicators):
            languages.append("EN")

        return languages if languages else ["DE"]

    def _extract_concepts(self, question: str, domains: list[LegalDomain]) -> list[str]:
        """Extract legal concepts based on domains."""
        concepts = []

        concept_map = {
            LegalDomain.CONTRACT: [
                "Vertragsabschluss",
                "Vertragserfüllung",
                "Vertragsverletzung",
                "Leistungsstörung",
                "Mängelhaftung",
                "Gewährleistung",
            ],
            LegalDomain.TORT: [
                "Kausalzusammenhang",
                "Widerrechtlichkeit",
                "Verschulden",
                "Schaden",
                "Haftungsvoraussetzungen",
            ],
            LegalDomain.EMPLOYMENT: [
                "Arbeitspflicht",
                "Fürsorgepflicht",
                "Treuepflicht",
                "Kündigungsschutz",
                "Lohnanspruch",
            ],
        }

        for domain in domains:
            if domain in concept_map:
                for concept in concept_map[domain]:
                    if concept.lower() in question.lower():
                        concepts.append(concept)

        return list(set(concepts))

    # -------------------------------------------------------------------------
    # Step 2: PLAN
    # -------------------------------------------------------------------------

    async def _plan(
        self,
        params: ResearchParameters,
        depth: ResearchDepth,
        max_sources: int,
    ) -> SearchStrategy:
        """Create optimized search strategy."""
        start = datetime.utcnow()

        # Configure sources based on jurisdiction
        sources = self._configure_sources(params)

        # Generate queries for each source
        queries = self._generate_queries(params, sources)

        # Configure parallel execution
        parallel_config = {
            ResearchDepth.QUICK: 3,
            ResearchDepth.STANDARD: 5,
            ResearchDepth.DEEP: 8,
        }

        strategy = SearchStrategy(
            sources=sources,
            queries=queries,
            relevance_threshold=0.5,
            max_total_results=max_sources,
            parallel_limit=parallel_config[depth],
        )

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        self._record_action(
            ActionType.ANALYZE,
            "Created search strategy",
            inputs={"depth": depth.value, "max_sources": max_sources},
            outputs={
                "sources_count": len(sources),
                "queries_count": len(queries),
            },
            duration_ms=duration_ms,
        )

        self.update_state("strategy", strategy)
        return strategy

    def _configure_sources(self, params: ResearchParameters) -> list[SearchSource]:
        """Configure search sources based on parameters."""
        sources = []

        # Always include BGE (Federal Supreme Court)
        if params.jurisdiction_federal:
            sources.append(
                SearchSource(
                    name="BGE",
                    priority=1,
                    expected_volume=30,
                    mcp_server="bge-search",
                    search_method="search",
                )
            )

        # Add cantonal sources
        for canton in params.jurisdiction_cantons:
            sources.append(
                SearchSource(
                    name=f"Cantonal-{canton}",
                    priority=2,
                    expected_volume=20,
                    mcp_server="cantonal-courts",
                    search_method="search",
                )
            )

        # Add unified search as fallback
        sources.append(
            SearchSource(
                name="Entscheidsuche",
                priority=3,
                expected_volume=50,
                mcp_server="entscheidsuche",
                search_method="search",
            )
        )

        return sources

    def _generate_queries(
        self,
        params: ResearchParameters,
        sources: list[SearchSource],
    ) -> list[SearchQuery]:
        """Generate search queries for each source."""
        queries = []

        # Build base query from key terms
        base_query = " ".join(params.key_terms[:5])

        # Add statute references if present
        if params.statute_references:
            statute_query = " OR ".join(params.statute_references)
        else:
            statute_query = ""

        for source in sources:
            query_text = base_query
            if statute_query:
                query_text = f"({base_query}) AND ({statute_query})"

            filters: dict[str, Any] = {}
            if params.time_range_from:
                filters["date_from"] = params.time_range_from.isoformat()
            if params.time_range_to:
                filters["date_to"] = params.time_range_to.isoformat()

            for lang in params.languages:
                queries.append(
                    SearchQuery(
                        source=source.name,
                        query=query_text,
                        filters=filters,
                        language=lang,
                        max_results=source.expected_volume,
                    )
                )

        return queries

    async def _confirm_strategy(self, strategy: SearchStrategy) -> None:
        """Request user confirmation of search strategy (CAUTIOUS mode)."""
        summary = (
            f"Search strategy:\n"
            f"- {len(strategy.sources)} sources\n"
            f"- {len(strategy.queries)} queries\n"
            f"- Max {strategy.max_total_results} results\n"
            f"Proceed?"
        )
        await self.request_user_confirmation(summary)

    async def _show_strategy_summary(self, strategy: SearchStrategy) -> None:
        """Show strategy summary (BALANCED mode)."""
        # In real implementation, this would display to user
        pass

    # -------------------------------------------------------------------------
    # Step 3: SEARCH
    # -------------------------------------------------------------------------

    async def _search(self, strategy: SearchStrategy) -> SearchResults:
        """Execute parallel searches across sources."""
        start = datetime.utcnow()

        all_results: list[RawResult] = []
        by_source: dict[str, list[RawResult]] = {}

        # Execute queries in parallel batches
        for i in range(0, len(strategy.queries), strategy.parallel_limit):
            batch = strategy.queries[i : i + strategy.parallel_limit]
            batch_results = await asyncio.gather(
                *[self._execute_query(q) for q in batch], return_exceptions=True
            )

            for query, result in zip(batch, batch_results, strict=True):
                if isinstance(result, BaseException):
                    self._handle_search_error(result, query.source)
                    continue

                source_results = self._parse_results(result, query.source)
                all_results.extend(source_results)

                if query.source not in by_source:
                    by_source[query.source] = []
                by_source[query.source].extend(source_results)

                self.record_source_access(query.source)

        # Deduplicate results
        deduplicated = self._deduplicate_results(all_results)

        # Sort by relevance
        deduplicated.sort(key=lambda r: r.relevance_score, reverse=True)

        # Limit to max results
        deduplicated = deduplicated[: strategy.max_total_results]

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        self._record_action(
            ActionType.SEARCH,
            "Executed parallel searches",
            inputs={"queries": len(strategy.queries)},
            outputs={
                "total_found": len(all_results),
                "deduplicated": len(deduplicated),
            },
            duration_ms=duration_ms,
        )

        return SearchResults(
            results=deduplicated,
            by_source=by_source,
            total_found=len(all_results),
            deduplicated_count=len(deduplicated),
            processing_time_ms=duration_ms,
        )

    async def _execute_query(self, query: SearchQuery) -> dict[str, Any]:
        """Execute a single search query via MCP."""
        # Map source to MCP server
        mcp_server = self._get_mcp_server(query.source)

        return await self.mcp_client.call(
            mcp_server,
            "search",
            {
                "query": query.query,
                "filters": query.filters,
                "language": query.language,
                "limit": query.max_results,
            },
        )

    def _get_mcp_server(self, source_name: str) -> str:
        """Map source name to MCP server."""
        if source_name == "BGE":
            return "bge-search"
        elif source_name.startswith("Cantonal-"):
            return "cantonal-courts"
        else:
            return "entscheidsuche"

    def _parse_results(self, response: dict[str, Any], source: str) -> list[RawResult]:
        """Parse MCP response into RawResult objects."""
        results = []
        for item in response.get("results", []):
            try:
                date = None
                if item.get("date"):
                    date = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))

                results.append(
                    RawResult(
                        id=item.get("id", ""),
                        title=item.get("title", ""),
                        citation=item.get("citation", ""),
                        date=date,
                        court=item.get("court", ""),
                        summary=item.get("summary", ""),
                        relevance_score=float(item.get("relevance_score", 0.5)),
                        source=source,
                        full_text_url=item.get("full_text_url"),
                        language=item.get("language", "DE"),
                    )
                )
            except (KeyError, ValueError):
                # Skip malformed results
                pass

        return results

    def _deduplicate_results(self, results: list[RawResult]) -> list[RawResult]:
        """Remove duplicate results based on citation."""
        seen_citations: set[str] = set()
        unique = []

        for result in results:
            citation_key = result.citation.lower().strip()
            if citation_key and citation_key not in seen_citations:
                seen_citations.add(citation_key)
                unique.append(result)

        return unique

    def _handle_search_error(self, error: BaseException, source: str) -> None:
        """Handle search error for a source."""
        self._errors.append(
            {
                "type": "search_error",
                "source": source,
                "message": str(error),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    # -------------------------------------------------------------------------
    # Step 4: VERIFY
    # -------------------------------------------------------------------------

    async def _verify(self, results: SearchResults) -> VerificationReport:
        """Verify all citations in results."""
        start = datetime.utcnow()

        verified: list[VerifiedCitation] = []
        outdated: list[VerifiedCitation] = []
        errors: list[dict[str, str]] = []

        # Extract unique citations
        citations = list({r.citation for r in results.results if r.citation})

        # Verify each citation
        for citation in citations:
            try:
                response = await self.mcp_client.call(
                    "legal-citations", "verify", {"citation": citation}
                )

                verified_citation = VerifiedCitation(
                    citation=citation,
                    is_valid=response.get("verified", False),
                    is_current=response.get("is_current", True),
                    formatted=response.get("formatted", citation),
                    court=response.get("court", ""),
                    date=None,
                    issues=response.get("issues", []),
                )

                if verified_citation.is_current:
                    verified.append(verified_citation)
                else:
                    outdated.append(verified_citation)

            except Exception as e:
                errors.append(
                    {
                        "citation": citation,
                        "error": str(e),
                    }
                )

        # Calculate accuracy
        total = len(verified) + len(outdated) + len(errors)
        accuracy = len(verified) / total if total > 0 else 1.0

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        self._record_action(
            ActionType.ANALYZE,
            "Verified citations",
            inputs={"citations_count": len(citations)},
            outputs={
                "verified": len(verified),
                "outdated": len(outdated),
                "errors": len(errors),
                "accuracy": accuracy,
            },
            duration_ms=duration_ms,
        )

        return VerificationReport(
            verified=verified,
            outdated=outdated,
            errors=errors,
            overall_accuracy=accuracy,
        )

    async def _report_verification(self, report: VerificationReport) -> None:
        """Report verification results to user."""
        if report.outdated or report.errors:
            message = (
                f"Citation verification complete:\n"
                f"- {len(report.verified)} verified\n"
                f"- {len(report.outdated)} outdated\n"
                f"- {len(report.errors)} errors\n"
                f"Continue with synthesis?"
            )
            await self.request_user_confirmation(message)

    # -------------------------------------------------------------------------
    # Step 5: SYNTHESIZE
    # -------------------------------------------------------------------------

    async def _synthesize(
        self,
        results: SearchResults,
        verification: VerificationReport,
        params: ResearchParameters,
    ) -> Synthesis:
        """Analyze findings and create synthesis."""
        start = datetime.utcnow()

        # Group results by legal issue
        grouped = self._group_by_issue(results.results, params)

        # Generate findings
        findings = []
        for issue, issue_results in grouped.items():
            finding = self._generate_finding(issue, issue_results, verification)
            findings.append(finding)

        # Build precedent chain
        precedent_chain = self._build_precedent_chain(results.results)

        # Identify conflicts
        conflicts = self._identify_conflicts(findings)

        # Identify gaps
        gaps = self._identify_gaps(params, findings)

        # Generate recommendations
        recommendations = self._generate_recommendations(findings, gaps)

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        self._record_action(
            ActionType.ANALYZE,
            "Synthesized research findings",
            inputs={"results_count": len(results.results)},
            outputs={
                "findings": len(findings),
                "conflicts": len(conflicts),
                "gaps": len(gaps),
            },
            duration_ms=duration_ms,
        )

        return Synthesis(
            key_findings=findings,
            precedent_chain=precedent_chain,
            conflicts=conflicts,
            gaps=gaps,
            recommendations=recommendations,
        )

    def _group_by_issue(
        self,
        results: list[RawResult],
        params: ResearchParameters,
    ) -> dict[str, list[RawResult]]:
        """Group results by legal issue."""
        grouped: dict[str, list[RawResult]] = {}

        for result in results:
            # Simple grouping by domain - could be enhanced with NLP
            for domain in params.legal_domains:
                issue = domain.value
                if issue not in grouped:
                    grouped[issue] = []
                grouped[issue].append(result)

        return grouped

    def _generate_finding(
        self,
        issue: str,
        results: list[RawResult],
        verification: VerificationReport,
    ) -> Finding:
        """Generate a finding for an issue."""
        # Get verified citations for this issue
        result_citations = [r.citation for r in results]
        verified_citations = [
            v.formatted for v in verification.verified if v.citation in result_citations
        ]

        # Calculate confidence based on number of sources
        confidence = min(len(verified_citations) / 5, 1.0)

        # Generate conclusion (simplified - would use LLM in production)
        if results:
            conclusion = (
                f"Based on {len(results)} precedents, the legal position on {issue} is established."
            )
        else:
            conclusion = f"No clear precedent found for {issue}."

        return Finding(
            issue=issue,
            conclusion=conclusion,
            supporting_citations=verified_citations[:5],
            confidence=confidence,
        )

    def _build_precedent_chain(self, results: list[RawResult]) -> list[str]:
        """Build chronological precedent chain."""
        dated_results = [r for r in results if r.date]
        dated_results.sort(key=lambda r: r.date or datetime.min)
        return [r.citation for r in dated_results[:10]]

    def _identify_conflicts(self, findings: list[Finding]) -> list[dict[str, Any]]:
        """Identify conflicting findings."""
        # Simplified - would use more sophisticated analysis
        return []

    def _identify_gaps(
        self,
        params: ResearchParameters,
        findings: list[Finding],
    ) -> list[str]:
        """Identify gaps in research."""
        gaps = []

        # Check if all domains are covered
        covered_issues = {f.issue for f in findings}
        for domain in params.legal_domains:
            if domain.value not in covered_issues:
                gaps.append(f"No findings for {domain.value}")

        # Check confidence levels
        low_confidence = [f for f in findings if f.confidence < 0.5]
        for finding in low_confidence:
            gaps.append(f"Low confidence for {finding.issue}")

        return gaps

    def _generate_recommendations(
        self,
        findings: list[Finding],
        gaps: list[str],
    ) -> list[str]:
        """Generate recommendations for next steps."""
        recommendations = []

        if gaps:
            recommendations.append("Consider additional research to address gaps")

        low_confidence = [f for f in findings if f.confidence < 0.7]
        if low_confidence:
            recommendations.append("Consult doctrine for low-confidence findings")

        return recommendations

    # -------------------------------------------------------------------------
    # Step 6: DELIVER
    # -------------------------------------------------------------------------

    async def _deliver(
        self,
        synthesis: Synthesis,
        params: ResearchParameters,
        results: SearchResults,
        verification: VerificationReport,
    ) -> ResearchMemo:
        """Generate final research memo."""
        start = datetime.utcnow()

        # Generate executive summary
        executive_summary = self._generate_executive_summary(synthesis, params)

        # Generate methodology section
        methodology = self._generate_methodology(params, results)

        # Compile limitations
        limitations = self._compile_limitations(results, verification)

        # Generate next steps
        next_steps = synthesis.recommendations.copy()
        if synthesis.gaps:
            next_steps.append("Address identified research gaps")

        # Compile metadata
        metadata = {
            "research_date": datetime.utcnow().isoformat(),
            "question": params.original_question,
            "sources_searched": len(results.by_source),
            "total_results": results.total_found,
            "verified_citations": len(verification.verified),
            "processing_time_ms": results.processing_time_ms,
            "autonomy_mode": self.autonomy_mode.value,
        }

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        self._record_action(
            ActionType.GENERATE,
            "Generated research memo",
            inputs={},
            outputs={"sections": 6},
            duration_ms=duration_ms,
        )

        memo = ResearchMemo(
            title=f"Research Memo: {params.original_question[:50]}...",
            executive_summary=executive_summary,
            methodology=methodology,
            findings=synthesis.key_findings,
            citations=verification.verified,
            limitations=limitations,
            next_steps=next_steps,
            metadata=metadata,
        )

        self.record_document_write("research_memo")
        return memo

    def _generate_executive_summary(
        self,
        synthesis: Synthesis,
        params: ResearchParameters,
    ) -> str:
        """Generate executive summary."""
        findings_summary = []
        for finding in synthesis.key_findings:
            if finding.confidence >= 0.7:
                findings_summary.append(finding.conclusion)

        if findings_summary:
            return " ".join(findings_summary[:3])
        else:
            return (
                f"Research completed for: {params.original_question}. See detailed findings below."
            )

    def _generate_methodology(
        self,
        params: ResearchParameters,
        results: SearchResults,
    ) -> str:
        """Generate methodology section."""
        sources = list(results.by_source.keys())
        return (
            f"This research analyzed {results.total_found} sources from {len(sources)} databases "
            f"({', '.join(sources)}). Results were deduplicated and verified for currency. "
            f"Languages: {', '.join(params.languages)}."
        )

    def _compile_limitations(
        self,
        results: SearchResults,
        verification: VerificationReport,
    ) -> list[str]:
        """Compile research limitations."""
        limitations = []

        if verification.outdated:
            limitations.append(f"{len(verification.outdated)} citations may be outdated")

        if verification.errors:
            limitations.append(f"{len(verification.errors)} citations could not be verified")

        if self._errors:
            limitations.append("Some sources were unavailable during research")

        return limitations

    # -------------------------------------------------------------------------
    # Result Creation
    # -------------------------------------------------------------------------

    def _create_success_result(self, memo: ResearchMemo) -> AgentResult[ResearchMemo]:
        """Create successful result."""
        execution_time = int(
            (datetime.utcnow() - (self._start_time or datetime.utcnow())).total_seconds() * 1000
        )

        audit_log = self._create_audit_log(
            AgentOutcome.SUCCESS,
            ["research_memo"],
        )

        return AgentResult(
            success=True,
            outcome=AgentOutcome.SUCCESS,
            deliverable=memo,
            partial_results=None,
            error_message=None,
            audit_log=audit_log,
            execution_time_ms=execution_time,
        )

    def _create_failure_result(self, error: Exception) -> AgentResult[ResearchMemo]:
        """Create failure result."""
        execution_time = int(
            (datetime.utcnow() - (self._start_time or datetime.utcnow())).total_seconds() * 1000
        )

        # Try to get partial results - not implemented yet
        partial: ResearchMemo | None = None

        audit_log = self._create_audit_log(
            AgentOutcome.FAILED,
            [],
        )

        return AgentResult(
            success=False,
            outcome=AgentOutcome.FAILED,
            deliverable=None,
            partial_results=partial,
            error_message=str(error),
            audit_log=audit_log,
            execution_time_ms=execution_time,
        )
