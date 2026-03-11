# BetterCallClaude v1.2 Implementation Workflow
# StrategistAgent & DrafterAgent

**Target Release**: v1.2.0
**Development Mode**: PARALLEL (both agents simultaneously)
**Pattern Reference**: ResearcherAgent (src/agents/researcher.py)

---

## Executive Summary

This workflow defines the structured implementation plan for two new agents:
- **StrategistAgent**: Litigation strategy development with risk assessment
- **DrafterAgent**: Legal document generation with Swiss law compliance

Both agents are designed as **independent tools with orchestration capacity** - they work standalone AND can be chained via AgentOrchestrator.

---

## Phase 1: Foundation & Infrastructure (Days 1-3)

### 1.1 Shared Data Models

**File**: `src/agents/models/shared.py`

```python
# Priority: HIGH
# Dependencies: None

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

class Language(Enum):
    """Supported languages with Swiss focus"""
    DE = "de"  # German (Deutsch)
    FR = "fr"  # French (Français)
    IT = "it"  # Italian (Italiano)
    EN = "en"  # English

class RiskLevel(Enum):
    """Risk assessment levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class Jurisdiction(Enum):
    """Swiss jurisdictions"""
    FEDERAL = "federal"
    ZH = "zurich"
    BE = "bern"
    GE = "geneva"
    BS = "basel"
    VD = "vaud"
    TI = "ticino"

@dataclass
class LegalParty:
    """Party in legal proceedings"""
    name: str
    role: str  # plaintiff, defendant, appellant, etc.
    representation: Optional[str] = None
    language_preference: Language = Language.DE

@dataclass
class CaseFacts:
    """Structured case facts for analysis"""
    summary: str
    key_events: List[Dict[str, Any]] = field(default_factory=list)
    disputed_facts: List[str] = field(default_factory=list)
    undisputed_facts: List[str] = field(default_factory=list)
    evidence_available: List[str] = field(default_factory=list)
```

**Tasks**:
- [ ] Create `src/agents/models/` directory
- [ ] Create `shared.py` with base enums and dataclasses
- [ ] Add comprehensive docstrings (DE/FR/IT terminology)
- [ ] Write unit tests: `tests/agents/models/test_shared.py`

### 1.2 StrategistAgent Models

**File**: `src/agents/models/strategist.py`

```python
# Priority: HIGH
# Dependencies: shared.py

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .shared import RiskLevel, Language, Jurisdiction, CaseFacts

class StrategyType(Enum):
    """Litigation strategy types"""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    SETTLEMENT = "settlement"
    HYBRID = "hybrid"

class SuccessProbability(Enum):
    """Case success probability bands"""
    EXCELLENT = "excellent"  # >80%
    GOOD = "good"           # 60-80%
    MODERATE = "moderate"   # 40-60%
    CHALLENGING = "challenging"  # 20-40%
    UNLIKELY = "unlikely"   # <20%

@dataclass
class RiskAssessment:
    """Comprehensive risk evaluation"""
    overall_level: RiskLevel
    litigation_risk: RiskLevel
    cost_risk: RiskLevel
    reputation_risk: RiskLevel
    factors: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    confidence_score: float = 0.0

@dataclass
class CostEstimate:
    """Legal cost estimation"""
    minimum_chf: float
    maximum_chf: float
    most_likely_chf: float
    breakdown: Dict[str, float] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)

@dataclass
class StrategyRecommendation:
    """Complete strategy output"""
    strategy_type: StrategyType
    success_probability: SuccessProbability
    risk_assessment: RiskAssessment
    cost_estimate: CostEstimate
    recommended_actions: List[str] = field(default_factory=list)
    alternative_strategies: List[Dict] = field(default_factory=list)
    key_arguments: List[str] = field(default_factory=list)
    weak_points: List[str] = field(default_factory=list)
    timeline_weeks: int = 0
    checkpoints: List[str] = field(default_factory=list)
```

**Tasks**:
- [ ] Create `strategist.py` with strategy-specific models
- [ ] Include cost estimation structures
- [ ] Add opponent analysis models
- [ ] Write unit tests: `tests/agents/models/test_strategist.py`

### 1.3 DrafterAgent Models

**File**: `src/agents/models/drafter.py`

```python
# Priority: HIGH
# Dependencies: shared.py

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .shared import Language, Jurisdiction

class DocumentType(Enum):
    """Swiss legal document types"""
    # Submissions
    KLAGESCHRIFT = "klageschrift"         # Statement of claim
    KLAGEANTWORT = "klageantwort"         # Statement of defense
    REPLIK = "replik"                     # Reply
    DUPLIK = "duplik"                     # Rejoinder
    BERUFUNG = "berufung"                 # Appeal
    BESCHWERDE = "beschwerde"             # Complaint/Appeal

    # Legal opinions
    RECHTSGUTACHTEN = "rechtsgutachten"   # Legal opinion
    MEMORANDUM = "memorandum"             # Legal memo

    # Contracts
    VERTRAG = "vertrag"                   # Contract
    VEREINBARUNG = "vereinbarung"         # Agreement

    # Correspondence
    MAHNUNG = "mahnung"                   # Formal notice/reminder
    KUENDIGUNG = "kuendigung"             # Termination notice

class DocumentSection(Enum):
    """Standard document sections"""
    RUBRUM = "rubrum"           # Header with parties
    RECHTSBEGEHREN = "rechtsbegehren"  # Legal requests/prayers
    SACHVERHALT = "sachverhalt"        # Facts
    RECHTLICHES = "rechtliches"        # Legal arguments
    BEWEISMITTEL = "beweismittel"      # Evidence
    SCHLUSSFOLGERUNG = "schlussfolgerung"  # Conclusion

@dataclass
class DocumentMetadata:
    """Document metadata"""
    document_type: DocumentType
    language: Language
    jurisdiction: Jurisdiction
    case_reference: Optional[str] = None
    court: Optional[str] = None
    date_created: Optional[str] = None

@dataclass
class DocumentSection:
    """Individual document section"""
    section_type: str
    title: str
    content: str
    citations: List[str] = field(default_factory=list)
    footnotes: List[str] = field(default_factory=list)

@dataclass
class LegalDocument:
    """Complete legal document output"""
    metadata: DocumentMetadata
    sections: List[DocumentSection] = field(default_factory=list)
    full_text: str = ""
    word_count: int = 0
    page_estimate: int = 0
    citations_used: List[str] = field(default_factory=list)
    checkpoints_requested: List[str] = field(default_factory=list)
```

**Tasks**:
- [ ] Create `drafter.py` with document-specific models
- [ ] Define all Swiss document types with terminology
- [ ] Add section structures for each document type
- [ ] Write unit tests: `tests/agents/models/test_drafter.py`

### 1.4 Test Infrastructure

**Directory Structure**:
```
tests/agents/
├── __init__.py
├── conftest.py              # Shared fixtures
├── models/
│   ├── __init__.py
│   ├── test_shared.py
│   ├── test_strategist.py
│   └── test_drafter.py
├── test_strategist.py       # StrategistAgent tests
├── test_drafter.py          # DrafterAgent tests
└── test_orchestrator.py     # Orchestration tests
```

**Shared Fixtures** (`conftest.py`):
```python
import pytest
from src.agents.models.shared import Language, Jurisdiction, CaseFacts

@pytest.fixture
def sample_case_facts_de():
    """Sample case facts in German"""
    return CaseFacts(
        summary="Vertragsverletzung gemäss Art. 97 OR",
        key_events=[
            {"date": "2024-01-15", "event": "Vertragsabschluss"},
            {"date": "2024-03-20", "event": "Leistungsverzug"},
        ],
        disputed_facts=["Schadenshöhe", "Kausalität"],
        undisputed_facts=["Vertragsexistenz", "Nichtzahlung"],
        evidence_available=["Vertrag", "Korrespondenz", "Rechnungen"]
    )

@pytest.fixture
def sample_case_facts_fr():
    """Sample case facts in French"""
    return CaseFacts(
        summary="Violation du contrat selon l'art. 97 CO",
        ...
    )
```

**Tasks**:
- [ ] Create test directory structure
- [ ] Implement `conftest.py` with multilingual fixtures
- [ ] Add pytest markers for language-specific tests
- [ ] Verify test discovery with `pytest --collect-only`

---

## Phase 2: StrategistAgent Core (Days 4-8)

### 2.1 StrategistAgent Base Implementation

**File**: `src/agents/strategist.py`

```python
# Priority: HIGH
# Dependencies: base.py, models/strategist.py

from typing import Any, Optional, List, Dict
from dataclasses import dataclass
from src.agents.base import AgentBase, AgentResult, AutonomyMode, CaseContext
from src.agents.models.strategist import (
    StrategyType, StrategyRecommendation, RiskAssessment, CostEstimate
)
from src.agents.models.shared import Language, Jurisdiction, CaseFacts


class StrategistAgent(AgentBase):
    """
    Litigation strategy development agent.

    Analyzes case facts and develops comprehensive litigation strategies
    with risk assessment, cost estimation, and success probability analysis.

    Arbeitet auf Deutsch, Français, Italiano, English.
    """

    WORKFLOW_STEPS = [
        "ANALYZE",      # Analyze case facts and legal framework
        "ASSESS_RISK",  # Comprehensive risk evaluation
        "ESTIMATE",     # Cost-benefit analysis
        "STRATEGIZE",   # Develop strategy options
        "RECOMMEND",    # Final recommendation with checkpoints
    ]

    @property
    def agent_id(self) -> str:
        return "strategist"

    @property
    def agent_version(self) -> str:
        return "1.0.0"

    async def execute(
        self,
        task: str,
        case_facts: Optional[CaseFacts] = None,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        language: Language = Language.DE,
        include_alternatives: bool = True,
        **kwargs: Any,
    ) -> AgentResult[StrategyRecommendation]:
        """
        Execute strategy development workflow.

        Args:
            task: Strategy request description
            case_facts: Structured case information
            jurisdiction: Target jurisdiction
            language: Output language
            include_alternatives: Include alternative strategies

        Returns:
            AgentResult containing StrategyRecommendation
        """
        # Implementation follows ResearcherAgent pattern
        pass

    # HIGH PRIORITY METHODS
    async def analyze_case(self, facts: CaseFacts) -> Dict[str, Any]:
        """Analyze case facts and identify legal issues"""
        pass

    async def assess_risk(self, analysis: Dict) -> RiskAssessment:
        """Comprehensive risk evaluation"""
        pass

    async def estimate_costs(self, strategy: StrategyType) -> CostEstimate:
        """Cost-benefit analysis with CHF estimates"""
        pass

    async def develop_strategy(
        self,
        analysis: Dict,
        risk: RiskAssessment
    ) -> StrategyRecommendation:
        """Develop and recommend litigation strategy"""
        pass

    # MEDIUM PRIORITY METHODS
    async def analyze_opponent(self, opponent_info: Dict) -> Dict[str, Any]:
        """Analyze opposing party's likely strategy"""
        pass

    async def generate_timeline(self, strategy: StrategyType) -> List[Dict]:
        """Generate procedural timeline with milestones"""
        pass
```

**Tasks**:
- [ ] Create `strategist.py` following AgentBase pattern
- [ ] Implement `execute()` with checkpoint integration
- [ ] Add `analyze_case()` - HIGH priority
- [ ] Add `assess_risk()` - HIGH priority
- [ ] Add `estimate_costs()` - HIGH priority
- [ ] Add `develop_strategy()` - HIGH priority
- [ ] Add `analyze_opponent()` - MEDIUM priority
- [ ] Add `generate_timeline()` - MEDIUM priority

### 2.2 Risk Assessment Module

**File**: `src/agents/strategist/risk_assessment.py`

**Functionality**:
- Evaluate litigation risk (procedural, substantive)
- Assess cost risk (escalation potential)
- Evaluate reputation risk
- Generate mitigation strategies

**Tasks**:
- [ ] Create risk scoring algorithm
- [ ] Implement risk factor identification
- [ ] Add mitigation recommendation logic
- [ ] Write comprehensive tests

### 2.3 Cost-Benefit Module

**File**: `src/agents/strategist/cost_benefit.py`

**Functionality**:
- Calculate legal fees (hourly, flat fee estimates)
- Estimate court costs by jurisdiction
- Model settlement scenarios
- Compare cost vs. recovery potential

**Tasks**:
- [ ] Implement Swiss legal fee calculations
- [ ] Add court cost tables by jurisdiction
- [ ] Create settlement scenario modeling
- [ ] Write financial calculation tests

### 2.4 Checkpoint Integration for StrategistAgent

**High-Risk Strategy Checkpoints**:
```python
STRATEGY_CHECKPOINTS = {
    "risk_high": {
        "trigger": "risk_assessment.overall_level in [HIGH, VERY_HIGH]",
        "message": "⚠️ High-risk strategy identified. Review before proceeding.",
        "requires_confirmation": True,
    },
    "cost_significant": {
        "trigger": "cost_estimate.maximum_chf > 50000",
        "message": "💰 Significant cost projection. Confirm budget approval.",
        "requires_confirmation": True,
    },
    "strategy_aggressive": {
        "trigger": "strategy_type == AGGRESSIVE",
        "message": "⚔️ Aggressive strategy selected. Confirm approach.",
        "requires_confirmation": True,
    },
}
```

**Tasks**:
- [ ] Define checkpoint triggers for StrategistAgent
- [ ] Implement checkpoint creation in workflow
- [ ] Add user confirmation handling
- [ ] Test checkpoint behavior in each autonomy mode

---

## Phase 3: DrafterAgent Core (Days 4-8, PARALLEL)

### 3.1 DrafterAgent Base Implementation

**File**: `src/agents/drafter.py`

```python
# Priority: HIGH
# Dependencies: base.py, models/drafter.py

from typing import Any, Optional, List, Dict
from src.agents.base import AgentBase, AgentResult, AutonomyMode
from src.agents.models.drafter import (
    DocumentType, LegalDocument, DocumentMetadata, DocumentSection
)
from src.agents.models.shared import Language, Jurisdiction


class DrafterAgent(AgentBase):
    """
    Legal document generation agent.

    Generates Swiss legal documents with proper structure, citations,
    and formatting for court submissions and legal opinions.

    Supports: Klageschrift, Rechtsgutachten, Verträge, and more.
    """

    WORKFLOW_STEPS = [
        "UNDERSTAND",    # Parse requirements and context
        "STRUCTURE",     # Create document outline
        "DRAFT",         # Generate content section by section
        "CITE",          # Add proper legal citations
        "FORMAT",        # Apply Swiss legal formatting
        "REVIEW",        # Final review with checkpoints
    ]

    @property
    def agent_id(self) -> str:
        return "drafter"

    @property
    def agent_version(self) -> str:
        return "1.0.0"

    async def execute(
        self,
        task: str,
        document_type: DocumentType = DocumentType.MEMORANDUM,
        language: Language = Language.DE,
        jurisdiction: Jurisdiction = Jurisdiction.FEDERAL,
        case_context: Optional[Dict] = None,
        strategy_input: Optional[Dict] = None,  # From StrategistAgent
        **kwargs: Any,
    ) -> AgentResult[LegalDocument]:
        """
        Execute document generation workflow.

        Args:
            task: Document generation request
            document_type: Type of legal document
            language: Document language
            jurisdiction: Target jurisdiction
            case_context: Case facts and context
            strategy_input: Optional strategy from StrategistAgent

        Returns:
            AgentResult containing LegalDocument
        """
        pass

    # HIGH PRIORITY METHODS
    async def generate_structure(
        self,
        doc_type: DocumentType,
        language: Language
    ) -> List[DocumentSection]:
        """Generate document structure for document type"""
        pass

    async def draft_section(
        self,
        section_type: str,
        content_input: Dict,
        language: Language
    ) -> DocumentSection:
        """Draft individual document section"""
        pass

    async def add_citations(
        self,
        document: LegalDocument,
        citations: List[str]
    ) -> LegalDocument:
        """Add and format legal citations"""
        pass

    async def format_document(
        self,
        document: LegalDocument,
        jurisdiction: Jurisdiction
    ) -> LegalDocument:
        """Apply jurisdiction-specific formatting"""
        pass

    # MEDIUM PRIORITY METHODS
    async def generate_bilingual(
        self,
        document: LegalDocument,
        target_language: Language
    ) -> LegalDocument:
        """Generate bilingual version of document"""
        pass

    async def validate_citations(
        self,
        citations: List[str]
    ) -> List[Dict[str, Any]]:
        """Validate citation format and existence"""
        pass
```

**Tasks**:
- [ ] Create `drafter.py` following AgentBase pattern
- [ ] Implement `execute()` with section-by-section drafting
- [ ] Add `generate_structure()` - HIGH priority
- [ ] Add `draft_section()` - HIGH priority
- [ ] Add `add_citations()` - HIGH priority
- [ ] Add `format_document()` - HIGH priority
- [ ] Add `generate_bilingual()` - MEDIUM priority
- [ ] Add `validate_citations()` - MEDIUM priority

### 3.2 Document Templates

**Directory**: `src/agents/drafter/templates/`

```
templates/
├── de/
│   ├── klageschrift.yaml
│   ├── klageantwort.yaml
│   ├── rechtsgutachten.yaml
│   └── vertrag.yaml
├── fr/
│   ├── demande.yaml
│   ├── reponse.yaml
│   ├── avis_juridique.yaml
│   └── contrat.yaml
└── it/
    ├── atto_di_citazione.yaml
    ├── risposta.yaml
    ├── parere_legale.yaml
    └── contratto.yaml
```

**Template Structure**:
```yaml
# klageschrift.yaml
document_type: KLAGESCHRIFT
language: de
jurisdiction: federal

sections:
  - name: rubrum
    title: "Rubrum"
    required: true
    template: |
      An das {court}

      In Sachen
      {plaintiff}
      Kläger
      vertreten durch {representation}

      gegen

      {defendant}
      Beklagter

  - name: rechtsbegehren
    title: "Rechtsbegehren"
    required: true
    template: |
      1. {main_request}
      2. {cost_request}
      3. {procedural_request}

  - name: sachverhalt
    title: "Sachverhalt"
    required: true
    subsections:
      - "Einleitung"
      - "Chronologie der Ereignisse"
      - "Streitpunkte"

  - name: rechtliches
    title: "Rechtliches"
    required: true
    subsections:
      - "Anwendbares Recht"
      - "Rechtliche Würdigung"
      - "Subsumtion"
```

**Tasks**:
- [ ] Create template directory structure
- [ ] Implement German templates (Klageschrift, Klageantwort, Rechtsgutachten)
- [ ] Implement French templates (Demande, Réponse, Avis juridique)
- [ ] Implement Italian templates (Atto di citazione, Risposta, Parere legale)
- [ ] Add template loading and validation logic

### 3.3 Citation Integration

**File**: `src/agents/drafter/citations.py`

**Functionality**:
- Format BGE citations (BGE 123 III 456)
- Format cantonal citations
- Validate citation existence via MCP servers
- Generate footnotes and references

**Tasks**:
- [ ] Create citation formatter for Swiss standards
- [ ] Integrate with legal-citations MCP server
- [ ] Add citation validation logic
- [ ] Generate proper footnote formatting

### 3.4 Checkpoint Integration for DrafterAgent

**Long Document Checkpoints**:
```python
DRAFTER_CHECKPOINTS = {
    "section_complete": {
        "trigger": "section_count > 3",
        "message": "📄 Section completed. Review before continuing.",
        "requires_confirmation": False,  # Info only in BALANCED
    },
    "document_long": {
        "trigger": "word_count > 5000",
        "message": "📚 Document exceeds 5000 words. Review structure.",
        "requires_confirmation": True,
    },
    "citations_pending": {
        "trigger": "unverified_citations > 0",
        "message": "📖 Unverified citations detected. Validate before finalizing.",
        "requires_confirmation": True,
    },
}
```

**Tasks**:
- [ ] Define checkpoint triggers for DrafterAgent
- [ ] Implement section completion checkpoints
- [ ] Add document length monitoring
- [ ] Test checkpoint behavior across autonomy modes

---

## Phase 4: Integration & Orchestration (Days 9-11)

### 4.1 AgentOrchestrator

**File**: `src/agents/orchestrator.py`

```python
# Priority: HIGH
# Dependencies: base.py, researcher.py, strategist.py, drafter.py

from typing import Any, Optional, List, Dict, Type
from dataclasses import dataclass
from src.agents.base import AgentBase, AgentResult, AutonomyMode, CaseContext
from src.agents.researcher import ResearcherAgent
from src.agents.strategist import StrategistAgent
from src.agents.drafter import DrafterAgent


@dataclass
class OrchestrationStep:
    """Single step in orchestration pipeline"""
    agent_class: Type[AgentBase]
    task: str
    input_mapping: Dict[str, str]  # Map outputs from previous steps
    checkpoint: bool = False


class AgentOrchestrator:
    """
    Orchestrates multi-agent workflows.

    Chains Research → Strategy → Draft with data passing
    and checkpoint management between agents.
    """

    def __init__(
        self,
        autonomy_mode: AutonomyMode = AutonomyMode.CAUTIOUS,
        case_context: Optional[CaseContext] = None,
    ):
        self.autonomy_mode = autonomy_mode
        self.case_context = case_context
        self.step_results: Dict[str, AgentResult] = {}

    async def execute_pipeline(
        self,
        steps: List[OrchestrationStep],
    ) -> Dict[str, AgentResult]:
        """Execute multi-agent pipeline with data passing"""
        pass

    async def research_to_strategy(
        self,
        research_query: str,
        case_facts: Dict,
    ) -> AgentResult:
        """Research → Strategy pipeline"""
        pass

    async def strategy_to_draft(
        self,
        strategy: Dict,
        document_type: str,
    ) -> AgentResult:
        """Strategy → Draft pipeline"""
        pass

    async def full_pipeline(
        self,
        query: str,
        case_facts: Dict,
        document_type: str,
    ) -> Dict[str, AgentResult]:
        """Research → Strategy → Draft full pipeline"""
        pass
```

**Tasks**:
- [ ] Create `orchestrator.py` with pipeline management
- [ ] Implement data passing between agents
- [ ] Add checkpoint aggregation across agents
- [ ] Implement `research_to_strategy()` pipeline
- [ ] Implement `strategy_to_draft()` pipeline
- [ ] Implement `full_pipeline()` complete chain
- [ ] Write integration tests

### 4.2 Update Package Exports

**File**: `src/agents/__init__.py`

```python
# Agent Framework package
# v1.2.0 - StrategistAgent, DrafterAgent, Orchestration

from src.agents.base import (
    ActionType,
    AgentOutcome,
    AutonomyMode,
    CaseContext,
    Party,
    AgentBase,
    AgentResult,
)
from src.agents.researcher import (
    LegalDomain,
    ResearchDepth,
    ResearcherAgent,
    SearchStrategy,
)
from src.agents.strategist import (
    StrategistAgent,
    StrategyType,
    RiskLevel,
)
from src.agents.drafter import (
    DrafterAgent,
    DocumentType,
)
from src.agents.orchestrator import (
    AgentOrchestrator,
    OrchestrationStep,
)

__all__ = [
    # Base classes
    "ActionType",
    "AgentOutcome",
    "AutonomyMode",
    "CaseContext",
    "Party",
    "AgentBase",
    "AgentResult",
    # Researcher
    "LegalDomain",
    "ResearchDepth",
    "ResearcherAgent",
    "SearchStrategy",
    # Strategist (NEW)
    "StrategistAgent",
    "StrategyType",
    "RiskLevel",
    # Drafter (NEW)
    "DrafterAgent",
    "DocumentType",
    # Orchestrator (NEW)
    "AgentOrchestrator",
    "OrchestrationStep",
]
```

**Tasks**:
- [ ] Update `__init__.py` with new exports
- [ ] Verify all imports work correctly
- [ ] Update version to 1.2.0

### 4.3 Slash Commands

**File**: `.claude/commands/legal/agent-strategist.md`

```markdown
---
description: "Start StrategistAgent for litigation strategy development"
arguments:
  - name: mode
    description: "Autonomy mode: cautious, balanced, autonomous"
    default: "cautious"
  - name: language
    description: "Output language: de, fr, it, en"
    default: "de"
---

# StrategistAgent

Activate the StrategistAgent in $mode mode for litigation strategy development.

## Workflow
1. Analyze case facts
2. Assess risks (litigation, cost, reputation)
3. Estimate costs in CHF
4. Develop strategy recommendations
5. Present with checkpoints for high-risk decisions

Language: $language
```

**File**: `.claude/commands/legal/agent-drafter.md`

```markdown
---
description: "Start DrafterAgent for legal document generation"
arguments:
  - name: mode
    description: "Autonomy mode: cautious, balanced, autonomous"
    default: "cautious"
  - name: type
    description: "Document type: klageschrift, rechtsgutachten, vertrag, etc."
    default: "memorandum"
  - name: language
    description: "Document language: de, fr, it, en"
    default: "de"
---

# DrafterAgent

Activate the DrafterAgent in $mode mode for $type generation.

## Workflow
1. Parse requirements
2. Generate document structure
3. Draft sections with checkpoints
4. Add legal citations
5. Format for Swiss jurisdiction

Language: $language
```

**Tasks**:
- [ ] Create `agent-strategist.md` slash command
- [ ] Create `agent-drafter.md` slash command
- [ ] Update `agent-researcher.md` if needed
- [ ] Add orchestration command for full pipeline

---

## Phase 5: Multi-lingual & Polish (Days 12-14)

### 5.1 Language Detection

**File**: `src/agents/utils/language.py`

```python
from typing import Optional
from src.agents.models.shared import Language

def detect_language(text: str) -> Language:
    """
    Detect language from input text.

    Uses simple heuristics for Swiss legal context:
    - German markers: der, die, das, und, gemäss, Art.
    - French markers: le, la, les, et, selon, art.
    - Italian markers: il, la, le, e, secondo, art.
    """
    pass

def confirm_language_with_user(detected: Language) -> Language:
    """Confirm detected language with user in CAUTIOUS mode"""
    pass
```

**Tasks**:
- [ ] Implement language detection
- [ ] Add user confirmation in CAUTIOUS mode
- [ ] Support bilingual document generation
- [ ] Test with DE/FR/IT legal texts

### 5.2 Documentation Updates

**Tasks**:
- [ ] Update `README.md` with new agents
- [ ] Update `docs/AGENT_ARCHITECTURE.md`
- [ ] Update language-specific docs (DE, FR, IT)
- [ ] Add examples for each agent

### 5.3 Final Testing & Validation

**Test Categories**:
```
tests/agents/
├── test_strategist.py          # Unit tests
├── test_drafter.py             # Unit tests
├── test_orchestrator.py        # Integration tests
├── test_e2e_pipeline.py        # End-to-end tests
└── test_multilingual.py        # Language tests
```

**Tasks**:
- [ ] Complete unit test coverage (>80%)
- [ ] Integration tests for agent chaining
- [ ] E2E tests for full pipeline
- [ ] Multi-lingual tests (DE, FR, IT)
- [ ] Performance benchmarks
- [ ] CI/CD validation

---

## Appendix: File Creation Checklist

### New Files (Create)
```
src/agents/models/__init__.py
src/agents/models/shared.py
src/agents/models/strategist.py
src/agents/models/drafter.py

src/agents/strategist.py
src/agents/strategist/__init__.py (optional module)
src/agents/strategist/risk_assessment.py
src/agents/strategist/cost_benefit.py

src/agents/drafter.py
src/agents/drafter/__init__.py (optional module)
src/agents/drafter/templates/de/*.yaml
src/agents/drafter/templates/fr/*.yaml
src/agents/drafter/templates/it/*.yaml
src/agents/drafter/citations.py

src/agents/orchestrator.py
src/agents/utils/language.py

.claude/commands/legal/agent-strategist.md
.claude/commands/legal/agent-drafter.md

tests/agents/models/test_shared.py
tests/agents/models/test_strategist.py
tests/agents/models/test_drafter.py
tests/agents/test_strategist.py
tests/agents/test_drafter.py
tests/agents/test_orchestrator.py
tests/agents/test_e2e_pipeline.py
tests/agents/test_multilingual.py
```

### Existing Files (Modify)
```
src/agents/__init__.py          # Add new exports
docs/AGENT_ARCHITECTURE.md      # Update architecture docs
docs/command-reference.md       # Add new commands
docs/languages/de/erste-schritte.md
docs/languages/fr/guide-demarrage.md
docs/languages/it/guida-introduttiva.md
README.md                       # Add v1.2 features
pyproject.toml                  # Update version to 1.2.0
```

---

## Development Guidelines

### Parallel Development Strategy

Since StrategistAgent and DrafterAgent are independent, they can be developed simultaneously:

**Developer A (StrategistAgent)**:
- Phase 1.2: strategist.py models
- Phase 2: All StrategistAgent implementation
- Phase 4: Orchestrator (research_to_strategy)

**Developer B (DrafterAgent)**:
- Phase 1.3: drafter.py models
- Phase 3: All DrafterAgent implementation
- Phase 4: Orchestrator (strategy_to_draft)

**Shared**:
- Phase 1.1: shared.py models
- Phase 1.4: Test infrastructure
- Phase 4.2-4.3: Integration and commands
- Phase 5: Multi-lingual and polish

### Code Quality Standards

- **Type hints**: All functions fully typed
- **Docstrings**: Google-style with DE/FR/IT terminology
- **Tests**: pytest with >80% coverage
- **Linting**: black, isort, mypy strict
- **Documentation**: Inline and external docs

### Checkpoint Philosophy

- **CAUTIOUS**: Checkpoint at every decision point
- **BALANCED**: Checkpoint only for high-risk items
- **AUTONOMOUS**: Minimal checkpoints, comprehensive logging

---

*Generated for BetterCallClaude v1.2.0 - Parallel Agent Development*
*Created: 2024*
