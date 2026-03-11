# BetterCallClaude v1.3 Implementation Workflow
# Enhancement Release - Q1 2025

**Target Release**: v1.3.0
**Timeline**: Q1 2025 (January - March)
**Development Mode**: PHASED (6 two-week sprints)
**Dependencies**: v1.2.0 Agent Framework complete

---

## Executive Summary

This workflow defines the implementation plan for v1.3 Enhancement features:

| Feature | Complexity | Sprint | Priority |
|---------|------------|--------|----------|
| All 26 Swiss Cantons | Medium | 1 | 🔴 HIGH |
| Ollama Integration | Medium | 2 | 🔴 HIGH |
| Swisslex Integration | High | 3 | 🟡 MEDIUM |
| Weblaw Integration | High | 4 | 🟡 MEDIUM |
| Citation Network Analysis | Medium-High | 4-5 | 🟡 MEDIUM |
| Automated Research Reports | High | 5 | 🟡 MEDIUM |
| Practice Management Integration | Medium | 6 | 🟢 LOW |

**Key Dependencies**:
- Citation Network → requires database integrations
- Research Reports → requires cantons + databases + citations
- All features build on v1.2 Agent Framework

---

## Sprint Overview

```
Sprint 1 (Jan 6-19)     → Foundation: 26 Cantons + Ollama Research
Sprint 2 (Jan 20-Feb 2) → Local AI: Ollama Integration Complete
Sprint 3 (Feb 3-16)     → Data: Swisslex Integration
Sprint 4 (Feb 17-Mar 2) → Data: Weblaw + Citation Network Start
Sprint 5 (Mar 3-16)     → Intelligence: Citations + Research Reports
Sprint 6 (Mar 17-30)    → Business: Practice Management + Release
```

---

## Phase 1: Foundation (Sprint 1)

### 1.1 Complete Swiss Cantonal Coverage

**Current State**: 8 cantons implemented
- ZH (Zurich), GE (Geneva), VD (Vaud), TI (Ticino)
- BE (Bern), BS (Basel-Stadt), LU (Lucerne), AG (Aargau)

**Target**: All 26 cantons

**File**: `src/agents/models/shared.py`

```python
# Extend Jurisdiction enum
class Jurisdiction(Enum):
    """Swiss jurisdictions - All 26 cantons + Federal"""
    # Federal
    FEDERAL = "federal"

    # German-speaking cantons (existing)
    ZH = "zurich"
    BE = "bern"
    BS = "basel_stadt"
    LU = "lucerne"
    AG = "aargau"

    # German-speaking cantons (NEW)
    SG = "st_gallen"
    GR = "graubuenden"
    ZG = "zug"
    SO = "solothurn"
    TG = "thurgau"
    SZ = "schwyz"
    SH = "schaffhausen"
    AR = "appenzell_ar"
    AI = "appenzell_ir"
    OW = "obwalden"
    NW = "nidwalden"
    GL = "glarus"
    UR = "uri"
    BL = "basel_land"

    # French-speaking cantons (existing)
    GE = "geneva"
    VD = "vaud"

    # French-speaking cantons (NEW)
    NE = "neuchatel"
    FR = "fribourg"
    VS = "valais"
    JU = "jura"

    # Italian-speaking cantons (existing)
    TI = "ticino"

    @property
    def primary_language(self) -> "Language":
        """Primary official language for the canton"""
        french_cantons = {self.GE, self.VD, self.NE, self.JU}
        italian_cantons = {self.TI}
        bilingual_de_fr = {self.FR, self.VS, self.BE}  # FR has both
        trilingual = {self.GR}  # DE, IT, RM

        if self in french_cantons:
            return Language.FR
        elif self in italian_cantons:
            return Language.IT
        else:
            return Language.DE

    @property
    def court_hierarchy(self) -> Dict[str, str]:
        """Court structure for the canton"""
        # Returns dict with court names in all languages
        pass

    @property
    def procedural_code(self) -> str:
        """Applicable cantonal procedural code reference"""
        pass
```

**New File**: `src/agents/jurisdiction/cantons.py`

```python
"""
Swiss cantonal jurisdiction data and configuration.

Provides court hierarchies, procedural rules, and language mappings
for all 26 Swiss cantons plus federal jurisdiction.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from src.agents.models.shared import Jurisdiction, Language


@dataclass
class CourtInfo:
    """Information about a specific court"""
    name: Dict[str, str]  # Multilingual names
    level: str  # district, cantonal, supreme
    address: Optional[str] = None
    website: Optional[str] = None


@dataclass
class CantonConfig:
    """Complete configuration for a Swiss canton"""
    jurisdiction: Jurisdiction
    official_languages: List[Language]
    courts: List[CourtInfo]
    procedural_rules: Dict[str, str]
    filing_requirements: Dict[str, str]
    fee_schedules: Dict[str, float]


# Canton configurations
CANTON_CONFIGS: Dict[Jurisdiction, CantonConfig] = {
    Jurisdiction.ZH: CantonConfig(
        jurisdiction=Jurisdiction.ZH,
        official_languages=[Language.DE],
        courts=[
            CourtInfo(
                name={"de": "Bezirksgericht Zürich", "fr": "Tribunal de district de Zurich"},
                level="district",
            ),
            CourtInfo(
                name={"de": "Obergericht des Kantons Zürich", "fr": "Cour suprême du canton de Zurich"},
                level="cantonal_supreme",
            ),
            CourtInfo(
                name={"de": "Handelsgericht des Kantons Zürich", "fr": "Tribunal de commerce du canton de Zurich"},
                level="specialized",
            ),
        ],
        procedural_rules={
            "civil": "ZPO (Schweizerische Zivilprozessordnung)",
            "cantonal": "GOG ZH (Gerichtsorganisationsgesetz)",
        },
        filing_requirements={
            "format": "A4, einseitig oder doppelseitig",
            "copies": "Original + je 1 Kopie pro Partei",
            "language": "Deutsch",
        },
        fee_schedules={
            "filing_base": 800.0,
            "per_streitwert_percent": 0.01,
            "minimum": 200.0,
            "maximum": 100000.0,
        },
    ),
    # ... configurations for all 26 cantons
}


def get_canton_config(jurisdiction: Jurisdiction) -> CantonConfig:
    """Get configuration for a specific canton"""
    if jurisdiction not in CANTON_CONFIGS:
        raise ValueError(f"Unknown jurisdiction: {jurisdiction}")
    return CANTON_CONFIGS[jurisdiction]


def get_courts_for_jurisdiction(
    jurisdiction: Jurisdiction,
    level: Optional[str] = None
) -> List[CourtInfo]:
    """Get courts for a jurisdiction, optionally filtered by level"""
    config = get_canton_config(jurisdiction)
    if level:
        return [c for c in config.courts if c.level == level]
    return config.courts


def get_filing_fee(
    jurisdiction: Jurisdiction,
    streitwert: float
) -> float:
    """Calculate filing fee based on jurisdiction and amount in dispute"""
    config = get_canton_config(jurisdiction)
    fees = config.fee_schedules

    calculated = fees["filing_base"] + (streitwert * fees["per_streitwert_percent"])
    return max(fees["minimum"], min(calculated, fees["maximum"]))
```

**Tasks**:
- [ ] Extend `Jurisdiction` enum with all 18 missing cantons
- [ ] Add `primary_language` property for each canton
- [ ] Create `src/agents/jurisdiction/` module
- [ ] Implement `CantonConfig` dataclass
- [ ] Add court hierarchies for all cantons
- [ ] Add procedural rules references
- [ ] Add filing requirements per canton
- [ ] Add fee schedule calculations
- [ ] Write comprehensive tests for all cantons
- [ ] Update documentation with canton coverage

### 1.2 Ollama Integration Research

**File**: `docs/research/ollama_integration.md`

**Research Tasks**:
- [ ] Evaluate Ollama Python client library
- [ ] Identify compatible models for legal tasks
- [ ] Design fallback strategy (local → cloud)
- [ ] Plan privacy mode implementation
- [ ] Document model selection criteria

**Recommended Models for Legal Work**:
```yaml
recommended_models:
  general_reasoning:
    - llama3.1:70b  # Best overall reasoning
    - mixtral:8x7b  # Good balance of speed/quality

  swiss_german:
    - llama3.1:8b   # For Swiss German processing

  document_analysis:
    - llama3.1:70b  # Long context for documents

  quick_tasks:
    - llama3.1:8b   # Fast responses
    - phi3:medium   # Efficient for simple tasks
```

---

## Phase 2: Local AI (Sprint 2)

### 2.1 Ollama Client Implementation

**File**: `src/integrations/ollama/client.py`

```python
"""
Ollama integration for local LLM inference.

Provides privacy-first AI capabilities for sensitive legal work,
with graceful fallback to Claude when needed.
"""

from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
import httpx
from enum import Enum


class OllamaModel(Enum):
    """Supported Ollama models"""
    LLAMA3_70B = "llama3.1:70b"
    LLAMA3_8B = "llama3.1:8b"
    MIXTRAL = "mixtral:8x7b"
    PHI3 = "phi3:medium"


@dataclass
class OllamaConfig:
    """Ollama connection configuration"""
    host: str = "http://localhost:11434"
    timeout: float = 120.0
    default_model: OllamaModel = OllamaModel.LLAMA3_8B
    max_retries: int = 3


@dataclass
class OllamaResponse:
    """Structured response from Ollama"""
    content: str
    model: str
    tokens_used: int
    generation_time: float
    is_complete: bool


class OllamaClient:
    """
    Client for Ollama local LLM inference.

    Features:
    - Automatic model selection based on task
    - Streaming response support
    - Health checking and availability detection
    - Graceful degradation when unavailable
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self._http_client = httpx.AsyncClient(timeout=self.config.timeout)
        self._available: Optional[bool] = None
        self._available_models: List[str] = []

    async def is_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = await self._http_client.get(f"{self.config.host}/api/tags")
            if response.status_code == 200:
                self._available = True
                self._available_models = [
                    m["name"] for m in response.json().get("models", [])
                ]
                return True
        except Exception:
            pass
        self._available = False
        return False

    async def list_models(self) -> List[str]:
        """List available models"""
        if not await self.is_available():
            return []
        return self._available_models

    async def generate(
        self,
        prompt: str,
        model: Optional[OllamaModel] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> OllamaResponse:
        """
        Generate completion from Ollama.

        Args:
            prompt: User prompt
            model: Model to use (default from config)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            OllamaResponse with generated content
        """
        if not await self.is_available():
            raise OllamaUnavailableError("Ollama is not available")

        model_name = (model or self.config.default_model).value

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = await self._http_client.post(
            f"{self.config.host}/api/generate",
            json=payload,
        )

        data = response.json()
        return OllamaResponse(
            content=data.get("response", ""),
            model=model_name,
            tokens_used=data.get("eval_count", 0),
            generation_time=data.get("total_duration", 0) / 1e9,
            is_complete=data.get("done", False),
        )

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[OllamaModel] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream generation token by token"""
        # Implementation for streaming responses
        pass

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[OllamaModel] = None,
        **kwargs,
    ) -> OllamaResponse:
        """Chat completion with message history"""
        # Implementation for chat interface
        pass


class OllamaUnavailableError(Exception):
    """Raised when Ollama is not available"""
    pass
```

### 2.2 Privacy Mode Implementation

**File**: `src/integrations/ollama/privacy_mode.py`

```python
"""
Privacy mode for sensitive legal document processing.

Routes requests to local Ollama when privacy is required,
with automatic fallback to cloud when local is unavailable.
"""

from typing import Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass


class PrivacyLevel(Enum):
    """Document privacy classification"""
    PUBLIC = "public"           # Can use cloud
    CONFIDENTIAL = "confidential"  # Prefer local
    PRIVILEGED = "privileged"   # Local only, no fallback


@dataclass
class PrivacyConfig:
    """Privacy mode configuration"""
    default_level: PrivacyLevel = PrivacyLevel.CONFIDENTIAL
    allow_cloud_fallback: bool = True
    local_only_patterns: list = None  # Regex patterns that force local
    log_routing_decisions: bool = True


class PrivacyRouter:
    """
    Routes AI requests based on privacy requirements.

    Decision matrix:
    - PUBLIC → Cloud preferred (faster/better)
    - CONFIDENTIAL → Local preferred, cloud fallback allowed
    - PRIVILEGED → Local only, fail if unavailable
    """

    def __init__(
        self,
        ollama_client: "OllamaClient",
        config: Optional[PrivacyConfig] = None,
    ):
        self.ollama = ollama_client
        self.config = config or PrivacyConfig()

    async def route_request(
        self,
        prompt: str,
        privacy_level: Optional[PrivacyLevel] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Route request to appropriate backend.

        Returns:
            Dict with 'backend' ('local' or 'cloud') and 'response'
        """
        level = privacy_level or self.config.default_level

        if level == PrivacyLevel.PRIVILEGED:
            # Must use local, no fallback
            if not await self.ollama.is_available():
                raise PrivacyViolationError(
                    "Local LLM required for privileged content but Ollama unavailable"
                )
            return await self._route_local(prompt, **kwargs)

        elif level == PrivacyLevel.CONFIDENTIAL:
            # Try local first, fallback to cloud if allowed
            if await self.ollama.is_available():
                return await self._route_local(prompt, **kwargs)
            elif self.config.allow_cloud_fallback:
                return await self._route_cloud(prompt, **kwargs)
            else:
                raise PrivacyViolationError(
                    "Local LLM unavailable and cloud fallback disabled"
                )

        else:  # PUBLIC
            # Use cloud for best quality
            return await self._route_cloud(prompt, **kwargs)

    async def _route_local(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Route to local Ollama"""
        response = await self.ollama.generate(prompt, **kwargs)
        return {"backend": "local", "response": response}

    async def _route_cloud(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Route to cloud (Claude)"""
        # Integration point with existing Claude code
        return {"backend": "cloud", "response": None}


class PrivacyViolationError(Exception):
    """Raised when privacy requirements cannot be met"""
    pass
```

**Tasks**:
- [ ] Create `src/integrations/ollama/` module
- [ ] Implement `OllamaClient` with full API support
- [ ] Add streaming generation support
- [ ] Implement `PrivacyRouter` for request routing
- [ ] Add model selection based on task type
- [ ] Create health check and monitoring
- [ ] Write comprehensive tests
- [ ] Add CLI commands for Ollama management
- [ ] Document privacy modes and model recommendations

### 2.3 Database API Research (Parallel)

**File**: `docs/research/database_integrations.md`

**Swisslex Research**:
- [ ] Contact Swisslex for API documentation
- [ ] Evaluate authentication methods
- [ ] Document endpoint structure
- [ ] Assess pricing and licensing

**Weblaw Research**:
- [ ] Contact Weblaw for API access
- [ ] Document available endpoints
- [ ] Evaluate data coverage
- [ ] Compare with Swisslex offerings

---

## Phase 3: Swisslex Integration (Sprint 3)

### 3.1 Swisslex Client Implementation

**File**: `src/integrations/databases/swisslex.py`

```python
"""
Swisslex commercial legal database integration.

Provides access to Swiss legal documents, court decisions,
and legal literature through the Swisslex API.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import httpx


class SwisslexDocType(Enum):
    """Swisslex document types"""
    BGE = "bge"              # Federal Supreme Court decisions
    CANTONAL = "cantonal"    # Cantonal court decisions
    LEGISLATION = "legislation"
    LITERATURE = "literature"
    COMMENTARY = "commentary"


@dataclass
class SwisslexConfig:
    """Swisslex API configuration"""
    api_key: str
    base_url: str = "https://api.swisslex.ch/v1"
    timeout: float = 30.0
    max_results: int = 50


@dataclass
class SwisslexDocument:
    """Document from Swisslex"""
    id: str
    doc_type: SwisslexDocType
    title: str
    citation: str
    date: Optional[datetime]
    summary: Optional[str]
    full_text: Optional[str]
    url: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class SwisslexSearchResult:
    """Search results from Swisslex"""
    total_hits: int
    documents: List[SwisslexDocument]
    query: str
    filters_applied: Dict[str, Any]


class SwisslexClient:
    """
    Client for Swisslex legal database.

    Features:
    - Full-text search across Swiss legal sources
    - Citation lookup and validation
    - Document retrieval with metadata
    - Cross-reference discovery
    """

    def __init__(self, config: SwisslexConfig):
        self.config = config
        self._http_client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=config.timeout,
        )

    async def search(
        self,
        query: str,
        doc_types: Optional[List[SwisslexDocType]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        jurisdiction: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> SwisslexSearchResult:
        """
        Search Swisslex database.

        Args:
            query: Search query (supports Boolean operators)
            doc_types: Filter by document types
            date_from: Filter by start date
            date_to: Filter by end date
            jurisdiction: Filter by jurisdiction
            max_results: Maximum results to return

        Returns:
            SwisslexSearchResult with matching documents
        """
        params = {"q": query, "limit": max_results or self.config.max_results}

        if doc_types:
            params["types"] = ",".join(dt.value for dt in doc_types)
        if date_from:
            params["from"] = date_from.isoformat()
        if date_to:
            params["to"] = date_to.isoformat()
        if jurisdiction:
            params["jurisdiction"] = jurisdiction

        response = await self._http_client.get("/search", params=params)
        data = response.json()

        return SwisslexSearchResult(
            total_hits=data.get("total", 0),
            documents=[self._parse_document(d) for d in data.get("results", [])],
            query=query,
            filters_applied=params,
        )

    async def get_document(self, document_id: str) -> SwisslexDocument:
        """Retrieve full document by ID"""
        response = await self._http_client.get(f"/documents/{document_id}")
        return self._parse_document(response.json())

    async def lookup_citation(self, citation: str) -> Optional[SwisslexDocument]:
        """
        Look up document by citation.

        Supports formats:
        - BGE 123 III 456
        - ATF 123 III 456
        - SR 220
        """
        response = await self._http_client.get(
            "/citations/lookup",
            params={"citation": citation},
        )

        if response.status_code == 404:
            return None
        return self._parse_document(response.json())

    async def get_citing_documents(
        self,
        document_id: str,
        max_results: int = 20,
    ) -> List[SwisslexDocument]:
        """Get documents that cite this document"""
        response = await self._http_client.get(
            f"/documents/{document_id}/citing",
            params={"limit": max_results},
        )
        return [self._parse_document(d) for d in response.json().get("results", [])]

    async def get_cited_documents(
        self,
        document_id: str,
    ) -> List[SwisslexDocument]:
        """Get documents cited by this document"""
        response = await self._http_client.get(
            f"/documents/{document_id}/cited",
        )
        return [self._parse_document(d) for d in response.json().get("results", [])]

    def _parse_document(self, data: Dict) -> SwisslexDocument:
        """Parse API response into SwisslexDocument"""
        return SwisslexDocument(
            id=data.get("id", ""),
            doc_type=SwisslexDocType(data.get("type", "bge")),
            title=data.get("title", ""),
            citation=data.get("citation", ""),
            date=datetime.fromisoformat(data["date"]) if data.get("date") else None,
            summary=data.get("summary"),
            full_text=data.get("full_text"),
            url=data.get("url"),
            metadata=data.get("metadata", {}),
        )


class SwisslexError(Exception):
    """Swisslex API error"""
    pass
```

### 3.2 Citation Extraction Service

**File**: `src/integrations/databases/citation_extractor.py`

```python
"""
Extract and validate legal citations from documents.

Identifies Swiss legal citations in text and validates
them against Swisslex/Weblaw databases.
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CitationType(Enum):
    """Types of Swiss legal citations"""
    BGE = "bge"           # Bundesgerichtsentscheid
    ATF = "atf"           # Arrêt du Tribunal fédéral
    DTF = "dtf"           # Decisione del Tribunale federale
    SR = "sr"             # Systematische Rechtssammlung
    RS = "rs"             # Recueil systématique
    CANTONAL = "cantonal"  # Cantonal decision
    EU = "eu"             # EU law reference


@dataclass
class ExtractedCitation:
    """Citation extracted from text"""
    raw_text: str
    citation_type: CitationType
    normalized: str
    position: Tuple[int, int]  # Start, end position in text
    is_validated: bool = False
    validation_url: Optional[str] = None


class CitationExtractor:
    """
    Extract Swiss legal citations from text.

    Patterns recognized:
    - BGE 123 III 456 E. 2.1
    - ATF 123 III 456 consid. 2.1
    - Art. 97 OR
    - Art. 41 CO
    - SR 220
    - § 123 ZGB
    """

    # Citation patterns
    PATTERNS = {
        CitationType.BGE: [
            r'BGE\s+(\d{1,3})\s+([IV]+)\s+(\d+)(?:\s+E\.\s*([\d\.]+))?',
            r'BGer\s+(\d+[A-Z]_\d+/\d{4})',
        ],
        CitationType.ATF: [
            r'ATF\s+(\d{1,3})\s+([IV]+)\s+(\d+)(?:\s+consid\.\s*([\d\.]+))?',
        ],
        CitationType.SR: [
            r'SR\s+(\d{3}(?:\.\d+)*)',
            r'Art\.\s*(\d+[a-z]?)\s+(OR|ZGB|StGB|SchKG|BV)',
        ],
    }

    def extract_all(self, text: str) -> List[ExtractedCitation]:
        """Extract all citations from text"""
        citations = []

        for cite_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    citations.append(ExtractedCitation(
                        raw_text=match.group(0),
                        citation_type=cite_type,
                        normalized=self._normalize_citation(match, cite_type),
                        position=(match.start(), match.end()),
                    ))

        return sorted(citations, key=lambda c: c.position[0])

    def _normalize_citation(self, match: re.Match, cite_type: CitationType) -> str:
        """Normalize citation to standard format"""
        if cite_type == CitationType.BGE:
            return f"BGE {match.group(1)} {match.group(2)} {match.group(3)}"
        elif cite_type == CitationType.ATF:
            return f"ATF {match.group(1)} {match.group(2)} {match.group(3)}"
        elif cite_type == CitationType.SR:
            return match.group(0)
        return match.group(0)

    async def validate_citations(
        self,
        citations: List[ExtractedCitation],
        swisslex_client: "SwisslexClient",
    ) -> List[ExtractedCitation]:
        """Validate citations against Swisslex"""
        validated = []
        for citation in citations:
            doc = await swisslex_client.lookup_citation(citation.normalized)
            citation.is_validated = doc is not None
            if doc:
                citation.validation_url = doc.url
            validated.append(citation)
        return validated
```

**Tasks**:
- [ ] Create `src/integrations/databases/` module
- [ ] Implement `SwisslexClient` with full API coverage
- [ ] Add authentication handling
- [ ] Implement citation lookup
- [ ] Add cross-reference discovery
- [ ] Create `CitationExtractor` for text analysis
- [ ] Write comprehensive tests with mocked API
- [ ] Document authentication setup
- [ ] Handle API errors gracefully

---

## Phase 4: Weblaw & Citation Network (Sprint 4)

### 4.1 Weblaw Client Implementation

**File**: `src/integrations/databases/weblaw.py`

```python
"""
Weblaw legal database integration.

Similar structure to Swisslex, providing access to
Swiss legal documents through Weblaw API.
"""

# Similar structure to SwisslexClient
# Implementation details TBD based on Weblaw API documentation
```

### 4.2 Citation Network Analysis

**File**: `src/analysis/citation_network.py`

```python
"""
Citation network analysis for Swiss legal documents.

Builds and analyzes citation graphs to identify:
- Influential precedents
- Citation patterns
- Legal doctrine evolution
- Related case clusters
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx


@dataclass
class CitationNode:
    """Node in citation graph"""
    document_id: str
    citation: str
    doc_type: str
    date: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationEdge:
    """Edge in citation graph (citation relationship)"""
    from_doc: str
    to_doc: str
    context: Optional[str] = None  # Text around citation
    section: Optional[str] = None  # Section where cited


@dataclass
class CitationMetrics:
    """Metrics for a document in the citation network"""
    document_id: str
    in_degree: int          # Number of documents citing this
    out_degree: int         # Number of documents cited
    pagerank: float         # PageRank score
    hub_score: float        # HITS hub score
    authority_score: float  # HITS authority score
    betweenness: float      # Betweenness centrality


class CitationNetwork:
    """
    Analyze citation relationships between legal documents.

    Features:
    - Build citation graphs from document collections
    - Calculate influence metrics (PageRank, HITS)
    - Find citation paths between documents
    - Cluster related documents
    - Track doctrine evolution over time
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._nodes: Dict[str, CitationNode] = {}
        self._edges: List[CitationEdge] = []

    def add_document(self, node: CitationNode) -> None:
        """Add document to citation network"""
        self._nodes[node.document_id] = node
        self.graph.add_node(
            node.document_id,
            citation=node.citation,
            doc_type=node.doc_type,
            date=node.date,
        )

    def add_citation(self, edge: CitationEdge) -> None:
        """Add citation relationship"""
        self._edges.append(edge)
        self.graph.add_edge(
            edge.from_doc,
            edge.to_doc,
            context=edge.context,
            section=edge.section,
        )

    def calculate_metrics(self, document_id: str) -> CitationMetrics:
        """Calculate all metrics for a document"""
        pagerank = nx.pagerank(self.graph)
        hits = nx.hits(self.graph)
        betweenness = nx.betweenness_centrality(self.graph)

        return CitationMetrics(
            document_id=document_id,
            in_degree=self.graph.in_degree(document_id),
            out_degree=self.graph.out_degree(document_id),
            pagerank=pagerank.get(document_id, 0.0),
            hub_score=hits[0].get(document_id, 0.0),
            authority_score=hits[1].get(document_id, 0.0),
            betweenness=betweenness.get(document_id, 0.0),
        )

    def find_most_influential(
        self,
        n: int = 10,
        metric: str = "pagerank",
    ) -> List[Tuple[str, float]]:
        """Find most influential documents by metric"""
        if metric == "pagerank":
            scores = nx.pagerank(self.graph)
        elif metric == "in_degree":
            scores = dict(self.graph.in_degree())
        elif metric == "authority":
            _, scores = nx.hits(self.graph)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]

    def find_citation_path(
        self,
        from_doc: str,
        to_doc: str,
    ) -> Optional[List[str]]:
        """Find shortest citation path between two documents"""
        try:
            return nx.shortest_path(self.graph, from_doc, to_doc)
        except nx.NetworkXNoPath:
            return None

    def get_citing_documents(
        self,
        document_id: str,
        depth: int = 1,
    ) -> Set[str]:
        """Get all documents citing this document up to depth"""
        citing = set()
        current_level = {document_id}

        for _ in range(depth):
            next_level = set()
            for doc in current_level:
                predecessors = set(self.graph.predecessors(doc))
                next_level.update(predecessors - citing)
            citing.update(next_level)
            current_level = next_level

        return citing

    def get_cited_documents(
        self,
        document_id: str,
        depth: int = 1,
    ) -> Set[str]:
        """Get all documents cited by this document up to depth"""
        cited = set()
        current_level = {document_id}

        for _ in range(depth):
            next_level = set()
            for doc in current_level:
                successors = set(self.graph.successors(doc))
                next_level.update(successors - cited)
            cited.update(next_level)
            current_level = next_level

        return cited

    def cluster_by_topic(
        self,
        n_clusters: int = 5,
    ) -> Dict[int, List[str]]:
        """Cluster documents by citation patterns"""
        # Use community detection algorithm
        communities = nx.community.louvain_communities(
            self.graph.to_undirected()
        )
        return {i: list(c) for i, c in enumerate(communities)}

    def export_for_visualization(self) -> Dict[str, Any]:
        """Export network for D3.js or similar visualization"""
        return {
            "nodes": [
                {
                    "id": node_id,
                    "citation": data.get("citation", ""),
                    "type": data.get("doc_type", ""),
                }
                for node_id, data in self.graph.nodes(data=True)
            ],
            "links": [
                {"source": u, "target": v}
                for u, v in self.graph.edges()
            ],
        }
```

**Tasks**:
- [ ] Implement `WeblawClient` (similar to Swisslex)
- [ ] Create `CitationNetwork` graph analysis
- [ ] Add influence metrics (PageRank, HITS)
- [ ] Implement citation path finding
- [ ] Add document clustering
- [ ] Create visualization export
- [ ] Write comprehensive tests
- [ ] Document network analysis capabilities

---

## Phase 5: Research Reports (Sprint 5)

### 5.1 Automated Research Report Generator

**File**: `src/reports/research_report.py`

```python
"""
Automated legal research report generation.

Combines canton data, database searches, citation analysis,
and agent outputs into comprehensive research reports.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ReportSection(Enum):
    """Standard report sections"""
    EXECUTIVE_SUMMARY = "executive_summary"
    LEGAL_FRAMEWORK = "legal_framework"
    CASE_LAW_ANALYSIS = "case_law_analysis"
    DOCTRINE = "doctrine"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATIONS = "recommendations"
    APPENDICES = "appendices"


@dataclass
class ReportConfig:
    """Report generation configuration"""
    title: str
    language: str = "de"
    sections: List[ReportSection] = field(default_factory=list)
    include_citations: bool = True
    include_network_analysis: bool = False
    max_pages: int = 20
    format: str = "markdown"  # markdown, pdf, docx


@dataclass
class ResearchReport:
    """Generated research report"""
    config: ReportConfig
    sections: Dict[str, str]
    citations: List[str]
    metadata: Dict[str, Any]
    generated_at: datetime
    word_count: int


class ResearchReportGenerator:
    """
    Generate comprehensive legal research reports.

    Integrates:
    - StrategistAgent analysis
    - DrafterAgent formatting
    - Swisslex/Weblaw searches
    - Citation network analysis
    - Cantonal jurisdiction data
    """

    def __init__(
        self,
        strategist: "StrategistAgent",
        drafter: "DrafterAgent",
        swisslex: Optional["SwisslexClient"] = None,
        weblaw: Optional["WeblawClient"] = None,
        citation_network: Optional["CitationNetwork"] = None,
    ):
        self.strategist = strategist
        self.drafter = drafter
        self.swisslex = swisslex
        self.weblaw = weblaw
        self.citation_network = citation_network

    async def generate(
        self,
        topic: str,
        config: ReportConfig,
        case_facts: Optional[Dict] = None,
    ) -> ResearchReport:
        """
        Generate complete research report.

        Args:
            topic: Research topic/question
            config: Report configuration
            case_facts: Optional case context

        Returns:
            Complete ResearchReport
        """
        sections = {}
        citations = []

        # 1. Research phase - gather data
        search_results = await self._gather_sources(topic)

        # 2. Analysis phase - use agents
        analysis = await self._analyze_sources(search_results, case_facts)

        # 3. Generation phase - create sections
        for section in config.sections:
            content = await self._generate_section(
                section,
                analysis,
                config.language,
            )
            sections[section.value] = content
            citations.extend(self._extract_citations(content))

        # 4. Finalization
        return ResearchReport(
            config=config,
            sections=sections,
            citations=list(set(citations)),
            metadata={
                "topic": topic,
                "sources_consulted": len(search_results),
            },
            generated_at=datetime.now(),
            word_count=sum(len(s.split()) for s in sections.values()),
        )

    async def _gather_sources(self, topic: str) -> List[Dict]:
        """Gather sources from all available databases"""
        results = []

        if self.swisslex:
            swisslex_results = await self.swisslex.search(topic)
            results.extend([{"source": "swisslex", "doc": d} for d in swisslex_results.documents])

        if self.weblaw:
            weblaw_results = await self.weblaw.search(topic)
            results.extend([{"source": "weblaw", "doc": d} for d in weblaw_results.documents])

        return results

    async def _analyze_sources(
        self,
        sources: List[Dict],
        case_facts: Optional[Dict],
    ) -> Dict[str, Any]:
        """Analyze sources using StrategistAgent"""
        # Use strategist to analyze legal issues
        # Use citation network to find influential precedents
        pass

    async def _generate_section(
        self,
        section: ReportSection,
        analysis: Dict,
        language: str,
    ) -> str:
        """Generate individual report section"""
        # Use DrafterAgent to generate formatted content
        pass

    def _extract_citations(self, content: str) -> List[str]:
        """Extract citations from generated content"""
        pass


# Report templates
REPORT_TEMPLATES = {
    "standard": ReportConfig(
        title="Legal Research Report",
        sections=[
            ReportSection.EXECUTIVE_SUMMARY,
            ReportSection.LEGAL_FRAMEWORK,
            ReportSection.CASE_LAW_ANALYSIS,
            ReportSection.RECOMMENDATIONS,
        ],
    ),
    "comprehensive": ReportConfig(
        title="Comprehensive Legal Analysis",
        sections=[
            ReportSection.EXECUTIVE_SUMMARY,
            ReportSection.LEGAL_FRAMEWORK,
            ReportSection.CASE_LAW_ANALYSIS,
            ReportSection.DOCTRINE,
            ReportSection.RISK_ASSESSMENT,
            ReportSection.RECOMMENDATIONS,
            ReportSection.APPENDICES,
        ],
        include_network_analysis=True,
        max_pages=50,
    ),
}
```

**Tasks**:
- [ ] Create `src/reports/` module
- [ ] Implement `ResearchReportGenerator`
- [ ] Add report templates (standard, comprehensive)
- [ ] Integrate with agents and databases
- [ ] Add citation management
- [ ] Support multiple output formats
- [ ] Write comprehensive tests
- [ ] Document report capabilities

---

## Phase 6: Practice Management & Release (Sprint 6)

### 6.1 Practice Management Integration

**File**: `src/integrations/practice_management/base.py`

```python
"""
Base classes for practice management system integration.

Provides common interface for Swiss PM systems:
- bexio (SME focus)
- Abacus (Enterprise)
- Kleos (Legal-specific)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PMProvider(Enum):
    """Supported practice management systems"""
    BEXIO = "bexio"
    ABACUS = "abacus"
    KLEOS = "kleos"
    GENERIC = "generic"


@dataclass
class TimeEntry:
    """Billable time entry"""
    description: str
    duration_minutes: int
    date: datetime
    matter_id: Optional[str] = None
    client_id: Optional[str] = None
    hourly_rate: Optional[float] = None
    billable: bool = True


@dataclass
class Matter:
    """Legal matter/case"""
    id: str
    name: str
    client_id: str
    status: str
    opened_date: datetime
    metadata: Dict[str, Any]


@dataclass
class Client:
    """Client record"""
    id: str
    name: str
    contact_email: Optional[str]
    matters: List[str]


class PracticeManagementClient(ABC):
    """Base class for PM integrations"""

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with PM system"""
        pass

    @abstractmethod
    async def log_time(self, entry: TimeEntry) -> str:
        """Log time entry, returns entry ID"""
        pass

    @abstractmethod
    async def get_matters(self, client_id: Optional[str] = None) -> List[Matter]:
        """Get matters, optionally filtered by client"""
        pass

    @abstractmethod
    async def get_clients(self) -> List[Client]:
        """Get all clients"""
        pass

    @abstractmethod
    async def create_matter(self, matter: Matter) -> str:
        """Create new matter, returns matter ID"""
        pass
```

**File**: `src/integrations/practice_management/bexio.py`

```python
"""
bexio practice management integration.

bexio is popular among Swiss SMEs and provides
REST API for time tracking and client management.
"""

from typing import Any, Dict, List, Optional
import httpx
from .base import PracticeManagementClient, TimeEntry, Matter, Client


class BexioClient(PracticeManagementClient):
    """
    bexio API client.

    API Documentation: https://docs.bexio.com/
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bexio.com/2.0"
        self._http_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def authenticate(self) -> bool:
        """Verify API key is valid"""
        try:
            response = await self._http_client.get("/company")
            return response.status_code == 200
        except Exception:
            return False

    async def log_time(self, entry: TimeEntry) -> str:
        """Log time entry to bexio"""
        payload = {
            "text": entry.description,
            "duration_hours": entry.duration_minutes / 60,
            "date": entry.date.isoformat(),
            "client_id": entry.client_id,
            "project_id": entry.matter_id,
            "billable": entry.billable,
        }

        response = await self._http_client.post("/timetracking", json=payload)
        return response.json().get("id", "")

    async def get_matters(self, client_id: Optional[str] = None) -> List[Matter]:
        """Get projects (matters) from bexio"""
        params = {}
        if client_id:
            params["contact_id"] = client_id

        response = await self._http_client.get("/project", params=params)

        return [
            Matter(
                id=str(p["id"]),
                name=p["name"],
                client_id=str(p.get("contact_id", "")),
                status=p.get("status", "active"),
                opened_date=p.get("start_date"),
                metadata=p,
            )
            for p in response.json()
        ]

    async def get_clients(self) -> List[Client]:
        """Get contacts (clients) from bexio"""
        response = await self._http_client.get("/contact")

        return [
            Client(
                id=str(c["id"]),
                name=c["name_1"],
                contact_email=c.get("mail"),
                matters=[],
            )
            for c in response.json()
        ]

    async def create_matter(self, matter: Matter) -> str:
        """Create project in bexio"""
        payload = {
            "name": matter.name,
            "contact_id": int(matter.client_id),
            "start_date": matter.opened_date.isoformat() if matter.opened_date else None,
        }

        response = await self._http_client.post("/project", json=payload)
        return str(response.json().get("id", ""))
```

**Tasks**:
- [ ] Create `src/integrations/practice_management/` module
- [ ] Implement `PracticeManagementClient` base class
- [ ] Implement `BexioClient` with full API support
- [ ] Add time tracking integration
- [ ] Add matter/client management
- [ ] Write comprehensive tests
- [ ] Document setup for each PM system

### 6.2 Release Preparation

**Tasks**:
- [ ] Update README.md with v1.3 features
- [ ] Update CHANGELOG.md
- [ ] Verify all tests pass (target: 80%+ coverage)
- [ ] Update pyproject.toml version to 1.3.0
- [ ] Create migration guide from v1.2
- [ ] Final documentation review
- [ ] CI/CD validation

---

## Appendix: File Creation Checklist

### New Files (Create)

```
# Phase 1: Foundation
src/agents/jurisdiction/__init__.py
src/agents/jurisdiction/cantons.py

# Phase 2: Ollama
src/integrations/__init__.py
src/integrations/ollama/__init__.py
src/integrations/ollama/client.py
src/integrations/ollama/privacy_mode.py

# Phase 3-4: Databases
src/integrations/databases/__init__.py
src/integrations/databases/swisslex.py
src/integrations/databases/weblaw.py
src/integrations/databases/citation_extractor.py

# Phase 4: Citation Network
src/analysis/__init__.py
src/analysis/citation_network.py

# Phase 5: Reports
src/reports/__init__.py
src/reports/research_report.py
src/reports/templates/standard.yaml
src/reports/templates/comprehensive.yaml

# Phase 6: Practice Management
src/integrations/practice_management/__init__.py
src/integrations/practice_management/base.py
src/integrations/practice_management/bexio.py
src/integrations/practice_management/abacus.py
src/integrations/practice_management/kleos.py

# Tests
tests/jurisdiction/test_cantons.py
tests/integrations/test_ollama.py
tests/integrations/test_swisslex.py
tests/integrations/test_weblaw.py
tests/analysis/test_citation_network.py
tests/reports/test_research_report.py
tests/integrations/test_practice_management.py
```

### Existing Files (Modify)

```
src/agents/models/shared.py          # Extend Jurisdiction enum
src/agents/__init__.py               # Add new exports
README.md                            # Add v1.3 features
CHANGELOG.md                         # Add v1.3 release notes
pyproject.toml                       # Update version to 1.3.0
docs/command-reference.md            # Add new commands
```

---

## Risk Mitigation Strategies

### High-Risk: Swisslex/Weblaw API Access

**Risk**: Commercial API access may require lengthy negotiations

**Mitigation**:
1. Begin API access discussions in Sprint 1
2. Develop mock API clients for testing
3. Fallback: Enhanced BGE web scraping
4. Modular design allows features to work without commercial DBs

### Medium-Risk: Practice Management Diversity

**Risk**: Many PM systems with varying API quality

**Mitigation**:
1. Start with bexio (best documented API)
2. Design abstract interface for easy expansion
3. Allow manual data export/import as fallback

### Low-Risk: Ollama Availability

**Risk**: Users may not have Ollama installed

**Mitigation**:
1. Clear installation documentation
2. Graceful fallback to cloud
3. Health check on startup

---

## Development Guidelines

### Code Quality Standards

- **Type hints**: All functions fully typed
- **Docstrings**: Google-style with usage examples
- **Tests**: pytest with >80% coverage
- **Linting**: black, ruff, mypy strict
- **Documentation**: Inline and external docs

### API Integration Patterns

```python
# Standard async client pattern
class ExternalClient:
    def __init__(self, config: Config):
        self.config = config
        self._http_client = httpx.AsyncClient(...)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._http_client.aclose()
```

### Environment Variables

```bash
# Ollama (optional)
OLLAMA_HOST=http://localhost:11434

# Commercial databases (optional)
SWISSLEX_API_KEY=your_key_here
WEBLAW_API_KEY=your_key_here

# Practice management (optional)
BEXIO_API_KEY=your_key_here
ABACUS_API_KEY=your_key_here
```

---

*Generated for BetterCallClaude v1.3.0 - Enhancement Release Q1 2025*
*Created: November 2024*
