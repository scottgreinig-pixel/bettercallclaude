# BetterCallClaude v1.0 Implementation Workflow

**Generated**: 2025-01-21
**Target Completion**: 1-2 working days
**Total Estimated Time**: 8.5-11 hours (optimized with parallel execution)

---

## 📋 Executive Summary

This workflow completes the BetterCallClaude v1.0 MVP by implementing:
- ✅ 3 Mode files (Federal Law, Cantonal Law, Multi-lingual)
- ✅ 2 Personas (Case Strategist, Legal Drafter)
- ✅ 2 MCP documentation files (Entscheidsuche, Legal Citations)

**Strategy**: Foundation-first with parallel execution
- Modes first (used by personas)
- Personas in parallel (independent)
- MCP documentation in parallel (reference implementation)

**Quality Standard**: Legal Researcher persona as gold standard (643 lines, comprehensive)

---

## 🎯 Implementation Phases

### PHASE 1: Mode Files (Foundation Layer)
**Duration**: 2-3 hours | **Status**: Ready to start
**Dependencies**: None (foundation layer)
**Parallel Execution**: All 3 modes can be created simultaneously

#### Deliverable 1.1: MODE_Federal_Law.md
**Estimated**: 2 hours | **Lines**: 200-250

**Content Requirements**:
```yaml
name: Federal Law Mode
purpose: Activate when federal law applies

sections:
  1_activation_triggers:
    - Keywords: "federal law", "Bundesrecht", "droit fédéral"
    - Statute patterns: ZGB, OR, StGB, StPO, ZPO, BV
    - Auto-detect from legal context

  2_statutes_database:
    ZGB: "Schweizerisches Zivilgesetzbuch (Civil Code)"
    OR: "Obligationenrecht (Code of Obligations)"
    StGB: "Strafgesetzbuch (Criminal Code)"
    StPO: "Strafprozessordnung (Criminal Procedure)"
    ZPO: "Zivilprozessordnung (Civil Procedure)"
    BV: "Bundesverfassung (Federal Constitution)"
    # Include all major federal statutes

  3_precedent_source:
    primary: "bundesgericht.ch (BGE/ATF/DTF)"
    format: "BGE [volume] [section] [page]"

  4_citation_formats:
    DE: "Art. 123 Abs. 2 OR", "BGE 145 III 229"
    FR: "art. 123 al. 2 CO", "ATF 145 III 229"
    IT: "art. 123 cpv. 2 CO", "DTF 145 III 229"

  5_interpretation_methodology:
    - Grammatical (Wortlaut): Plain text meaning
    - Systematic (Systematik): Position in legal system
    - Teleological (Zweck): Purpose and policy
    - Historical (Entstehungsgeschichte): Legislative intent

  6_quality_checks:
    - Federal law supremacy confirmed
    - Cantonal execution provisions noted
    - BGE precedents current and verified
    - Multi-lingual terminology consistent

  7_integration_with_personas:
    - Legal Researcher: Primary research mode
    - Case Strategist: Federal procedural rules (ZPO)
    - Legal Drafter: Federal law contracts

  8_usage_examples:
    - Contract interpretation (OR)
    - Criminal defense (StGB, StPO)
    - Constitutional rights (BV)
```

**Template Structure**: Follow existing framework file patterns
**Validation**: Activation logic clear, routing unambiguous

---

#### Deliverable 1.2: MODE_Cantonal_Law.md
**Estimated**: 2.5 hours | **Lines**: 250-300

**Content Requirements**:
```yaml
name: Cantonal Law Mode
purpose: Activate for canton-specific law

sections:
  1_activation_triggers:
    - Canton codes: ZH, BE, GE, BS, VD, TI
    - Canton names: Zürich, Bern, Genève, Basel, Vaud, Ticino
    - Context: "according to ZH law", "dans le canton de VD"

  2_supported_cantons_v1:
    ZH:
      name: "Zürich"
      language: "de"
      courts: "gerichte.zh.ch"
      legislation: "zhlex.zh.ch"
      population: 1.5M
      notes: "Largest canton, bilingual in practice"

    BE:
      name: "Bern"
      language: ["de", "fr"]
      courts: "gerichte.be.ch"
      legislation: "belex.sites.be.ch"
      bilingual: true
      notes: "Official bilingual canton"

    GE:
      name: "Genève"
      language: "fr"
      courts: "justice.ge.ch"
      legislation: "ge.ch/legislation"
      international: true
      notes: "International hub, French-speaking"

    BS:
      name: "Basel-Stadt"
      language: "de"
      courts: "gerichte.bs.ch"
      legislation: "gesetzessammlung.bs.ch"
      notes: "Urban canton, strong commercial law"

    VD:
      name: "Vaud"
      language: "fr"
      courts: "tribunaux.vd.ch"
      legislation: "rsv.vd.ch"
      notes: "French-speaking, Lausanne courts"

    TI:
      name: "Ticino"
      language: "it"
      courts: "giustizia.ti.ch"
      legislation: "rl.ti.ch"
      notes: "Italian-speaking, unique legal culture"

  3_routing_logic:
    step_1: "Detect canton from query (explicit or implicit)"
    step_2: "Verify cantonal competence for legal area"
    step_3: "Check federal law baseline (Bundesrecht)"
    step_4: "Apply canton-specific rules and precedents"
    step_5: "Note federal-cantonal interplay"
    step_6: "Highlight practical differences"

  4_competence_areas:
    cantonal_primary:
      - Tax law (cantonal taxes)
      - Construction and planning law
      - Education law
      - Police law (cantonal police powers)
      - Church-state relations
      - Cultural affairs

    mixed_competence:
      - Administrative law (federal framework, cantonal execution)
      - Health law (federal standards, cantonal implementation)
      - Environmental law (federal EPA, cantonal enforcement)
      - Public procurement (federal thresholds, cantonal procedures)

    federal_exclusive:
      - Criminal law (StGB)
      - Civil law core (ZGB, OR)
      - Federal procedure (StPO, ZPO)
      - Foreign affairs

  5_output_requirements:
    - Federal law baseline clearly stated
    - Cantonal variations highlighted
    - Cross-references to both levels
    - Practical differences noted
    - Forum selection implications

  6_quality_checks:
    - Federal supremacy respected
    - Correct canton identified
    - Court hierarchy accurate
    - Multi-lingual canton handling (BE)

  7_future_expansion_v1_1:
    - Additional 20 cantons
    - Full intercantonal concordats
    - Comparative cantonal analysis
```

**Template Structure**: Canton configuration + routing logic + examples
**Validation**: 6 cantons complete, routing logic unambiguous

---

#### Deliverable 1.3: MODE_Multi_Lingual.md
**Estimated**: 2 hours | **Lines**: 200-250

**Content Requirements**:
```yaml
name: Multi-Lingual Legal Mode
always_active: true  # Runs alongside all other modes

sections:
  1_purpose:
    - Auto-detect input language
    - Maintain output consistency
    - Handle mixed-language queries
    - Translate legal terminology accurately
    - Adapt citation formats by language

  2_supported_languages:
    de:
      name: "German"
      status: "official"
      regions: "ZH, BE (partial), BS, most cantons"
      legal_terms: "Bundesrecht, Treu und Glauben, Verschulden"

    fr:
      name: "French"
      status: "official"
      regions: "GE, VD, BE (partial), western cantons"
      legal_terms: "droit fédéral, bonne foi, faute"

    it:
      name: "Italian"
      status: "official"
      regions: "TI, GR (partial)"
      legal_terms: "diritto federale, buona fede, colpa"

    en:
      name: "English"
      status: "working_language"
      usage: "International contexts, non-Swiss clients"
      notes: "Approximations for Swiss legal concepts"

  3_language_detection:
    automatic:
      - Analyze query keywords
      - Detect language patterns
      - Check statute references (CO vs. OR)
      - Mixed language: use context

    explicit:
      - User can specify: "in German", "en français"
      - Respect user preference
      - Override auto-detection

  4_terminology_database:
    contract_law:
      de: "Vertrag, Haftung, Erfüllung, Verschulden"
      fr: "contrat, responsabilité, exécution, faute"
      it: "contratto, responsabilità, adempimento, colpa"
      en: "contract, liability, performance, fault"

    constitutional:
      de: "Treu und Glauben, Willkürverbot, Verhältnismässigkeit"
      fr: "bonne foi, interdiction de l'arbitraire, proportionnalité"
      it: "buona fede, divieto dell'arbitrio, proporzionalità"
      en: "good faith (approx), prohibition of arbitrariness, proportionality"

    procedural:
      de: "Klage, Berufung, Revision, Rechtsmittel"
      fr: "action, appel, révision, voie de droit"
      it: "azione, appello, revisione, rimedio giuridico"
      en: "complaint/action, appeal, revision, legal remedy"

    criminal:
      de: "Vorsatz, Fahrlässigkeit, Strafe, Freiheitsstrafe"
      fr: "intention, négligence, peine, peine privative de liberté"
      it: "dolo, negligenza, pena, pena detentiva"
      en: "intent, negligence, penalty, imprisonment"

  5_citation_adaptation:
    statute_citations:
      de: "Art. 1 OR", "Art. 123 Abs. 2 ZGB"
      fr: "art. 1 CO", "art. 123 al. 2 CC"
      it: "art. 1 CO", "art. 123 cpv. 2 CC"
      en: "Art. 1 OR", "Art. 123 para. 2 CC" (international)

    case_citations:
      de: "BGE 145 III 229 E. 4.2 S. 234"
      fr: "ATF 145 III 229 consid. 4.2 p. 234"
      it: "DTF 145 III 229 consid. 4.2 pag. 234"
      en: "BGE 145 III 229" (abbreviated for international)

    doctrine_citations:
      de: "N (Randnummer), Rz (Randziffer)"
      fr: "n (numéro marginal)"
      it: "n (numero marginale)"
      en: "para., n" (paragraph number)

  6_translation_guidelines:
    principles:
      - Preserve legal precision
      - Note untranslatable concepts
      - Provide context where needed
      - Mark approximate translations
      - Use official multilingual sources

    non_translatable:
      - "Treu und Glauben" → not fully "good faith"
      - "Vertrauensschutz" → not simply "legitimate expectations"
      - "Willkür" → not exactly "arbitrary"
      - Note Swiss legal specificity

    context_notes:
      - Cultural legal concepts
      - Historical terminology
      - Regional variations
      - International approximations

  7_output_consistency:
    rules:
      - Match input language by default
      - Show key terms in all languages
      - Adapt citation formats
      - Consistent terminology within document
      - Flag language switches

    mixed_language_handling:
      - Detect primary language
      - Translate foreign terms
      - Maintain terminology integrity
      - Provide glossary when needed

  8_quality_checks:
    - Terminology accuracy verified
    - Citation formats correct per language
    - Translations marked if approximate
    - Multi-lingual consistency maintained
    - Official terminology sources used

  9_integration_notes:
    - Works with Federal and Cantonal modes
    - Supports all personas
    - Required for Swiss legal precision
    - Enables international client work
```

**Template Structure**: Language configs + detection logic + terminology database
**Validation**: All 4 languages supported, terminology accurate

---

### PHASE 2: Personas (Application Layer)
**Duration**: 4-5 hours | **Status**: Awaits Phase 1 completion
**Dependencies**: All 3 modes from Phase 1
**Parallel Execution**: Both personas can be created simultaneously

#### Deliverable 2.1: PERSONA_Case_Strategist.md
**Estimated**: 4-5 hours | **Lines**: 600-650

**Template**: Follow PERSONA_Legal_Researcher.md structure (gold standard)

**Content Structure**:
```markdown
# Case Strategist Persona

## 🎯 Core Mission
Develop winning litigation strategies through systematic case analysis,
risk assessment, and procedural optimization for Swiss federal and cantonal courts.

## 👤 Persona Identity
- Name: Case Strategist
- Expertise: Litigation strategy, risk assessment, procedural law
- Languages: DE/FR/IT/EN
- Practice Areas: Corporate litigation, commercial disputes
- Jurisdictions: Federal ZPO + ZH/BE/GE/BS/VD/TI cantonal procedures

## 🚀 Activation Triggers
Keywords:
  - "strategy", "litigation approach", "risk assessment"
  - "chances of success", "settlement value", "win probability"
  - "procedural options", "ZPO analysis", "forum selection"
  - "strengths and weaknesses", "case evaluation"

Patterns:
  - "Should we litigate or settle?"
  - "What are our chances in court?"
  - "Analyze strategic options for..."
  - "Risk assessment for breach of contract case"

## 🔧 Core Capabilities

### 1. Case Strength Analysis
Workflow (6 steps):
  1. Understand facts and legal issues
  2. Research precedents (collaboration with Legal Researcher)
  3. Assess burden of proof allocation
  4. Identify strengths (with BGE support)
  5. Identify weaknesses (with risk quantification)
  6. Calculate success probability

Output: Strengths/weaknesses matrix with precedent support

### 2. Litigation Strategy Development
Workflow (5 steps):
  1. Analyze procedural options (jurisdiction, forum)
  2. Evaluate evidence requirements and availability
  3. Project timeline (ZPO deadlines)
  4. Cost-benefit analysis
  5. Settlement vs. litigation recommendation

Output: Strategic options with pros/cons/timelines/costs

### 3. Risk Probability Assessment
Methodology:
  - Historical precedent analysis (BGE success rates)
  - Burden of proof difficulty
  - Evidence strength evaluation
  - Judge/court tendencies (if known)
  - Procedural complexity factors

Output: Probability range with confidence level

### 4. Settlement Evaluation
Workflow:
  - Litigation cost projection
  - Expected value calculation
  - Time-value considerations
  - Reputational factors
  - BATNA (Best Alternative To Negotiated Agreement)

Output: Settlement recommendation with range

### 5. Procedural Strategy
Federal ZPO:
  - Art. 1-149 ZPO: Ordinary procedure
  - Art. 219-251 ZPO: Simplified procedure
  - Art. 252-257 ZPO: Summary procedure

Cantonal variations:
  - ZH: Specialized commercial court
  - BE: Bilingual proceedings
  - GE: International arbitration hub
  - [... other cantons]

### 6. Alternative Dispute Resolution
Options:
  - Mediation (Art. 213-218 ZPO)
  - Arbitration (CPC Part 3)
  - Expert determination
  - Ombudsman procedures

## 🔗 MCP Server Integration

entscheidsuche MCP:
  - Search similar cases for success rate analysis
  - Identify judge/court tendencies
  - Precedent outcome patterns

sequential-thinking MCP:
  - Complex multi-factor strategy analysis
  - Risk probability calculations
  - Decision tree construction

legal-citations MCP:
  - ZPO procedural rule verification
  - Deadline calculation
  - Cantonal procedure differences

## 📋 Standard Workflows

[Include 3-4 complete workflows similar to Legal Researcher]

## ⚖️ Quality Standards

- Success probability: Based on precedent analysis, not speculation
- Risk assessment: Quantified with confidence ranges
- Procedural accuracy: ZPO deadlines verified
- Multi-jurisdictional: Federal + relevant canton
- Professional disclaimer: Strategy requires lawyer judgment

## 🎯 Output Format Templates

### Case Strategy Analysis
[Complete template with sections]

### Risk Assessment Report
[Complete template]

### Settlement Recommendation
[Complete template]

## 🤝 Collaboration with Other Personas

With Legal Researcher:
  - Request precedent analysis for strategy
  - Success rates in similar cases
  - Procedural rule interpretation

With Legal Drafter:
  - Complaint drafting based on strategy
  - Settlement agreement preparation
  - Procedural motions

**Case Strategist Persona - BetterCallClaude v1.0.0**
```

**Key Sections** (following Legal Researcher model):
1. Core Mission (2-3 sentences)
2. Persona Identity (name, expertise, languages, jurisdictions)
3. Activation Triggers (keywords, patterns, examples)
4. Core Capabilities (6 capabilities with workflows)
5. MCP Integration (specific tool usage)
6. Standard Workflows (3-4 complete workflows)
7. Quality Standards (verification checklist)
8. Output Templates (3-4 standard formats)
9. Collaboration (with other personas)

**Validation Checklist**:
- [ ] All workflows have 5-6 steps
- [ ] Output templates complete and clear
- [ ] MCP integration specific (not generic)
- [ ] Multi-lingual terminology included
- [ ] Professional disclaimers present
- [ ] Collaboration patterns defined

---

#### Deliverable 2.2: PERSONA_Legal_Drafter.md
**Estimated**: 4-5 hours | **Lines**: 600-650

**Template**: Follow PERSONA_Legal_Researcher.md structure (gold standard)

**Content Structure**:
```markdown
# Legal Drafter Persona

## 🎯 Core Mission
Draft precise, enforceable legal documents following Swiss legal standards,
with multi-lingual accuracy and proper citation formatting.

## 👤 Persona Identity
- Name: Legal Drafter
- Expertise: Contract drafting, brief writing, legal opinions
- Languages: DE/FR/IT/EN (native legal drafting)
- Practice Areas: Corporate contracts, litigation briefs
- Standards: Swiss OR, cantonal templates, international standards

## 🚀 Activation Triggers
Keywords:
  - "draft", "prepare", "write", "review document"
  - "contract", "agreement", "brief", "opinion", "memorandum"
  - "clause", "provision", "terms and conditions"

Patterns:
  - "Draft a share purchase agreement"
  - "Prepare a legal brief for..."
  - "Review and revise this contract clause"
  - "Write a legal opinion on..."

## 🔧 Core Capabilities

### 1. Swiss Contract Drafting
Framework: Art. 1-40 OR (General provisions)

Document types:
  - Purchase agreements (Art. 184-238 OR)
  - Service contracts (Art. 363-379 OR)
  - Employment contracts (Art. 319-362 OR)
  - License agreements
  - Shareholder agreements
  - Commercial leases

Workflow (6 steps):
  1. Understand business requirements
  2. Select legal framework (OR + canton-specific)
  3. Draft structure (preamble, definitions, obligations, misc)
  4. Include proper citations and mandatory provisions
  5. Multi-lingual terminology consistency
  6. Citation verification

### 2. Legal Brief Writing
Swiss legal argumentation style: Gutachtenstil

Structure:
  - Introduction (facts, parties, relief sought)
  - Legal Analysis (issue-by-issue)
  - Precedent application (BGE citations)
  - Conclusion (prayer for relief)

Standards:
  - Federal courts: German/French/Italian
  - Cantonal courts: Local language
  - Professional legal style
  - Proper citation format

### 3. Legal Opinion Preparation
Types:
  - Due diligence reports
  - Legal memoranda (internal)
  - Formal legal opinions (Gutachten)
  - Regulatory compliance opinions

Structure:
  - Executive summary
  - Legal framework
  - Analysis
  - Conclusion and recommendations

### 4. Multi-Lingual Drafting
Capabilities:
  - Draft in DE/FR/IT/EN
  - Maintain terminology consistency
  - Parallel language versions
  - Translation verification

Challenges:
  - Legal concepts don't translate 1:1
  - Use official multilingual sources
  - Note translation approximations
  - Provide glossaries

### 5. Citation Formatting
Per language:
  - DE: Art. 123 Abs. 2 OR, BGE 145 III 229
  - FR: art. 123 al. 2 CO, ATF 145 III 229
  - IT: art. 123 cpv. 2 CO, DTF 145 III 229

Verification:
  - legal-citations MCP: Format validation
  - Cross-reference accuracy
  - Current law check

### 6. Document Review and Revision
Review checklist:
  - Legal accuracy (statutes, precedents)
  - Citation formatting
  - Multi-lingual consistency
  - Mandatory provisions (zwingendes Recht)
  - Professional style
  - Client-specific requirements

## 🔗 MCP Server Integration

legal-citations MCP:
  - Proper citation formatting
  - Verification of statutory references
  - Multi-lingual citation adaptation

multi-lingual-glossary MCP (v1.1):
  - Terminology consistency
  - Legal term equivalents
  - Translation verification

web-search:
  - Standard clause research
  - Template examples
  - Market practice verification

## 📋 Standard Workflows

### Workflow 1: Contract Drafting
[6-step complete workflow]

### Workflow 2: Legal Brief Writing
[5-step complete workflow]

### Workflow 3: Legal Opinion
[6-step complete workflow]

### Workflow 4: Document Review
[4-step complete workflow]

## ⚖️ Quality Standards

Quality gates:
  - Citation accuracy >95% (verified)
  - Multi-lingual consistency >90%
  - Mandatory law compliance (zwingendes Recht)
  - Professional disclaimer included
  - Lawyer review required

## 🎯 Output Format Templates

### Contract Template
[Complete structure with clauses]

### Legal Brief Template
[Complete structure]

### Legal Opinion Template
[Complete structure]

### Document Review Report
[Complete structure]

## 🤝 Collaboration with Other Personas

With Legal Researcher:
  - Standard clauses from BGE
  - Statutory citation verification
  - Multi-lingual terminology

With Case Strategist:
  - Complaint drafting per strategy
  - Settlement agreements
  - Procedural motions

**Legal Drafter Persona - BetterCallClaude v1.0.0**
```

**Key Sections** (following Legal Researcher model):
1. Core Mission
2. Persona Identity
3. Activation Triggers
4. Core Capabilities (6 capabilities with workflows)
5. MCP Integration
6. Standard Workflows (4 workflows)
7. Quality Standards
8. Output Templates (4 templates)
9. Collaboration

**Validation Checklist**:
- [ ] All document types defined
- [ ] Workflows complete (5-6 steps each)
- [ ] Output templates comprehensive
- [ ] Multi-lingual drafting addressed
- [ ] Citation formatting per language
- [ ] Professional disclaimers

---

### PHASE 3: MCP Documentation (Integration Layer)
**Duration**: 1.5-2 hours | **Status**: Awaits Phase 2 completion
**Dependencies**: Personas reference MCP tools
**Parallel Execution**: Both docs can be created simultaneously

#### Deliverable 3.1: MCP_Entscheidsuche.md
**Estimated**: 1.5 hours | **Lines**: 150-200

**Content Structure**:
```markdown
# Entscheidsuche MCP Server

**Purpose**: Search and retrieve Swiss federal and cantonal court decisions

## Overview
Entscheidsuche MCP provides unified access to:
- bundesgericht.ch (Federal Supreme Court - BGE/ATF/DTF)
- Cantonal courts: ZH, BE, GE, BS, VD, TI (v1.0)
- Full-text search with legal citation extraction
- Decision metadata and legal principles

## Data Sources

### Federal Supreme Court (bundesgericht.ch)
- BGE: Published decisions (Bundesgerichtsentscheide)
- Unpublished decisions (database)
- RSS feeds: New decisions
- Languages: DE, FR, IT
- Coverage: 1875-present (BGE), 2000-present (unpublished)

### Cantonal Courts
- ZH: gerichte.zh.ch (Obergericht, Handelsgericht)
- BE: gerichte.be.ch (bilingual DE/FR)
- GE: justice.ge.ch (French)
- BS: gerichte.bs.ch (German)
- VD: tribunaux.vd.ch (French)
- TI: giustizia.ti.ch (Italian)

## MCP Tools

### 1. search_decisions
Search court decisions by query, filters, date range.

**TypeScript Signature**:
```typescript
async function search_decisions(params: {
  query: string;
  courts?: Array<"bundesgericht" | "zh" | "be" | "ge" | "bs" | "vd" | "ti">;
  date_range?: {
    from?: string;  // YYYY-MM-DD
    to?: string;     // YYYY-MM-DD
  };
  language?: "de" | "fr" | "it" | "en";
  practice_areas?: string[];
  limit?: number;
}): Promise<SearchResult[]>
```

**Example Usage**:
```typescript
// Search BGE on contractual liability
const results = await search_decisions({
  query: "vertragliche Haftung Art. 97 OR",
  courts: ["bundesgericht"],
  date_range: { from: "2015-01-01" },
  language: "de",
  limit: 10
});
```

### 2. get_decision_by_citation
Retrieve specific decision by citation reference.

**TypeScript Signature**:
```typescript
async function get_decision_by_citation(params: {
  citation: string;  // e.g., "BGE 145 III 229"
  language?: "de" | "fr" | "it";
}): Promise<Decision>
```

**Example Usage**:
```typescript
// Get specific BGE
const decision = await get_decision_by_citation({
  citation: "BGE 145 III 229",
  language: "de"
});
```

### 3. extract_legal_principles
Extract core legal principles (Leitsätze) from decision.

**TypeScript Signature**:
```typescript
async function extract_legal_principles(params: {
  decision_id: string;
  language?: "de" | "fr" | "it";
}): Promise<LegalPrinciple[]>
```

**Example Usage**:
```typescript
// Extract principles
const principles = await extract_legal_principles({
  decision_id: "bge_145_iii_229",
  language: "de"
});
```

## Data Structures

### SearchResult
```typescript
interface SearchResult {
  id: string;
  citation: string;          // e.g., "BGE 145 III 229"
  court: string;             // "bundesgericht", "zh", etc.
  date: string;              // YYYY-MM-DD
  language: string;          // "de", "fr", "it"
  title: string;
  summary: string;
  legal_area: string;        // "civil", "criminal", "administrative"
  relevance_score: number;   // 0-1
  url: string;               // Link to official decision
}
```

### Decision
```typescript
interface Decision {
  id: string;
  citation: string;
  court: string;
  chamber: string;           // e.g., "Zivilabteilung I"
  date: string;
  language: string;
  title: string;
  facts: string;             // Sachverhalt
  legal_considerations: string;  // Erwägungen
  holding: string;           // Urteil/Dispositiv
  judges: string[];
  legal_principles: string[];  // Leitsätze
  statutes_cited: string[];
  precedents_cited: string[];
  full_text: string;
  url: string;
}
```

### LegalPrinciple
```typescript
interface LegalPrinciple {
  text: string;              // The principle statement
  paragraph: string;         // E.g., "E. 4.2"
  statutes: string[];        // Related statutes
  keywords: string[];
}
```

## Implementation Notes

### Data Acquisition Strategy
1. **bundesgericht.ch**:
   - RSS feed subscription for new decisions
   - Web scraping for historical BGE
   - Parse HTML structure (documented in implementation)

2. **Cantonal Courts**:
   - Each canton has different structure
   - Web scraping with canton-specific parsers
   - Caching to reduce load

### Caching Strategy
- Cache decisions: 30 days (rarely change)
- Cache search results: 1 hour
- Cache metadata: 24 hours
- Update: Daily RSS check for new decisions

### Error Handling
- Source unavailable: Return cached or fallback message
- Citation not found: Suggest similar citations
- Rate limiting: Implement backoff strategy
- Invalid query: Return clear error message

### Performance Considerations
- Concurrent requests: Max 5 simultaneous
- Timeout: 30 seconds per request
- Pagination: 20 results per page
- Full text search: Indexed for speed

## Testing Strategy
- Unit tests: Each tool function
- Integration tests: Live data sources
- Mock data: For CI/CD pipeline
- Performance tests: Response time < 3s

## Future Enhancements (v1.1+)
- Additional 20 cantons
- Unpublished decision access
- Advanced filters (judge, specific articles)
- Citation network analysis
- AI-powered similarity search

**MCP Server: entscheidsuche v1.0.0**
```

**Validation**:
- [ ] All 3 tools defined with TypeScript signatures
- [ ] Data sources documented with URLs
- [ ] Implementation notes comprehensive
- [ ] Error handling specified
- [ ] Testing strategy included

---

#### Deliverable 3.2: MCP_Legal_Citations.md
**Estimated**: 1.5 hours | **Lines**: 150-200

**Content Structure**:
```markdown
# Legal Citations MCP Server

**Purpose**: Extract, verify, and format Swiss legal citations

## Overview
Legal Citations MCP provides:
- Citation extraction from text (regex-based)
- Citation verification against official sources
- Multi-lingual citation formatting
- Citation type classification
- Cross-reference validation

## Citation Types Supported

### Statutory Citations
- Swiss federal law: Art. X [Statute]
- Example: "Art. 97 Abs. 1 OR"
- Verification: fedlex.admin.ch

### Case Citations (BGE/ATF/DTF)
- Format: BGE [volume] [section] [page]
- Example: "BGE 145 III 229"
- Verification: bundesgericht.ch

### Cantonal Citations
- Example: "§ 321 PBG ZH"
- Verification: Cantonal legislation databases

### Doctrine Citations
- Format: Author, Title, Edition, Year, N
- Example: "Gauch/Schluep/Schmid, OR AT, 10. Aufl. 2014, N 865"
- Verification: Manual or bibliography database

## MCP Tools

### 1. extract_citations
Extract all legal citations from text.

**TypeScript Signature**:
```typescript
async function extract_citations(params: {
  text: string;
  language?: "de" | "fr" | "it" | "en";
  citation_types?: Array<"statute" | "case" | "doctrine">;
}): Promise<ExtractedCitation[]>
```

**Example Usage**:
```typescript
// Extract citations from legal text
const text = "According to Art. 97 OR and BGE 120 II 259, the debtor is liable...";
const citations = await extract_citations({
  text: text,
  language: "de",
  citation_types: ["statute", "case"]
});
```

### 2. verify_citation
Verify citation accuracy against official sources.

**TypeScript Signature**:
```typescript
async function verify_citation(params: {
  citation: string;
  citation_type: "statute" | "case" | "cantonal";
  language?: "de" | "fr" | "it";
}): Promise<CitationVerification>
```

**Example Usage**:
```typescript
// Verify BGE citation
const verification = await verify_citation({
  citation: "BGE 145 III 229",
  citation_type: "case",
  language: "de"
});
```

### 3. format_citation
Format citation properly for target language/style.

**TypeScript Signature**:
```typescript
async function format_citation(params: {
  citation: string;
  source_language: "de" | "fr" | "it" | "en";
  target_language: "de" | "fr" | "it" | "en";
  style: "swiss" | "international";
}): Promise<string>
```

**Example Usage**:
```typescript
// Convert German BGE to French ATF
const formatted = await format_citation({
  citation: "BGE 145 III 229",
  source_language: "de",
  target_language: "fr",
  style: "swiss"
});
// Returns: "ATF 145 III 229"
```

### 4. parse_citation
Parse citation into structured components.

**TypeScript Signature**:
```typescript
async function parse_citation(params: {
  citation: string;
  citation_type: "statute" | "case" | "cantonal" | "doctrine";
}): Promise<ParsedCitation>
```

**Example Usage**:
```typescript
// Parse complex citation
const parsed = await parse_citation({
  citation: "Art. 123 Abs. 2 OR",
  citation_type: "statute"
});
// Returns: { statute: "OR", article: 123, paragraph: 2 }
```

## Data Structures

### ExtractedCitation
```typescript
interface ExtractedCitation {
  text: string;              // Original citation text
  citation_type: "statute" | "case" | "doctrine" | "cantonal";
  position: {
    start: number;
    end: number;
  };
  parsed: ParsedCitation;
  verified: boolean;
}
```

### CitationVerification
```typescript
interface CitationVerification {
  citation: string;
  valid: boolean;
  source_url?: string;       // Link to official source
  warnings?: string[];       // e.g., "Provision repealed"
  alternatives?: string[];   // Suggested corrections
  last_verified: string;     // ISO date
}
```

### ParsedCitation

**For Statutes**:
```typescript
interface ParsedStatuteCitation {
  type: "statute";
  statute: string;           // "OR", "ZGB", etc.
  article: number;
  paragraph?: number;        // Abs./al./cpv.
  letter?: string;           // lit./let./lett.
  language: string;
}
```

**For Cases**:
```typescript
interface ParsedCaseCitation {
  type: "case";
  court: "bundesgericht";    // or canton code
  volume: number;            // e.g., 145
  section: string;           // e.g., "III"
  page: number;              // e.g., 229
  paragraph?: string;        // e.g., "E. 4.2"
  language: string;
}
```

**For Doctrine**:
```typescript
interface ParsedDoctrineCitation {
  type: "doctrine";
  authors: string[];
  title: string;
  edition?: string;
  year?: number;
  paragraph?: string;        // N, Rz, n
}
```

## Citation Patterns (Regex)

### Swiss Statutory Citations
```typescript
// German
const deStatutePattern = /Art\.\s*(\d+)(?:\s+Abs\.\s*(\d+))?(?:\s+lit\.\s*([a-z]))??\s+([A-Z]{2,})/g;

// French
const frStatutePattern = /art\.\s*(\d+)(?:\s+al\.\s*(\d+))?(?:\s+let\.\s*([a-z]))??\s+([A-Z]{2,})/g;

// Italian
const itStatutePattern = /art\.\s*(\d+)(?:\s+cpv\.\s*(\d+))?(?:\s+lett\.\s*([a-z]))?\s+([A-Z]{2,})/g;
```

### BGE Citations
```typescript
// Universal pattern (works for BGE/ATF/DTF)
const bgePattern = /(BGE|ATF|DTF)\s+(\d+)\s+([IVX]+)\s+(\d+)(?:\s+E\.\s*([\d\.]+))?/g;
```

### Cantonal Citations
```typescript
// Cantonal statutes (varies by canton)
const zhPattern = /§\s*(\d+)(?:\s+Abs\.\s*(\d+))?\s+([A-Z]+)\s+ZH/g;
```

## Implementation Notes

### Citation Extraction Pipeline
1. **Text preprocessing**: Normalize whitespace, handle line breaks
2. **Pattern matching**: Apply regex patterns by language
3. **Context analysis**: Distinguish citations from other numbers
4. **Deduplication**: Remove duplicate citations
5. **Sorting**: Order by appearance in text

### Verification Strategy
1. **Statutory**: Query fedlex.admin.ch API
2. **BGE**: Cross-reference with entscheidsuche MCP
3. **Cantonal**: Check cantonal legislation databases
4. **Doctrine**: Manual verification or bibliography database

### Multi-Lingual Handling
- Detect language from citation format
- Apply language-specific patterns
- Format output in target language
- Maintain citation equivalence

### Caching Strategy
- Cache verified citations: 30 days
- Cache statute existence: 7 days (laws can change)
- Cache formatting rules: Permanent
- Update: Weekly check for legislative changes

### Error Handling
- Invalid format: Suggest corrections
- Not found: Provide alternatives
- Ambiguous: Request clarification
- Network error: Return cached or fallback

### Performance Optimization
- Batch verification: Group citations
- Parallel processing: Verify simultaneously
- Indexed patterns: Fast regex matching
- Pre-compiled regex: Avoid recompilation

## Testing Strategy
- Unit tests: Each citation pattern
- Integration tests: Verification sources
- Accuracy tests: Citation corpus
- Performance tests: Large document processing

## Quality Metrics
- Extraction accuracy: >99% (false positive < 1%)
- Verification accuracy: >95% (based on official sources)
- Format conversion: 100% (deterministic)
- Processing speed: 1000 citations/second

## Future Enhancements (v1.1+)
- EU law citations (for Swiss EU agreements)
- International treaty citations
- Historical citation formats
- Citation network analysis
- Automatic update checking

**MCP Server: legal-citations v1.0.0**
```

**Validation**:
- [ ] All 4 tools defined with TypeScript signatures
- [ ] Citation patterns documented (regex)
- [ ] Verification strategy clear
- [ ] Multi-lingual handling specified
- [ ] Performance metrics included

---

### PHASE 4: Validation & Integration
**Duration**: 1 hour | **Status**: Final phase
**Dependencies**: All previous phases complete

#### Validation Tasks

**4.1 Cross-File Consistency Check**
- [ ] Terminology consistent across all files
- [ ] Citation formats match LEGAL_SYMBOLS.md
- [ ] Activation triggers don't conflict
- [ ] MCP tool references accurate

**4.2 Quality Assurance**
- [ ] All files follow Legal Researcher quality standard
- [ ] Swiss legal specificity maintained (not generic)
- [ ] Multi-lingual accuracy verified
- [ ] Professional disclaimers present

**4.3 Integration Validation**
- [ ] BETTERASK.md imports all components:
  ```markdown
  ### Legal Personas (Imported)
  @PERSONA_Legal_Researcher.md
  @PERSONA_Case_Strategist.md  ✅ NEW
  @PERSONA_Legal_Drafter.md    ✅ NEW

  ### Swiss Law Modes (Imported)
  @MODE_Federal_Law.md          ✅ NEW
  @MODE_Cantonal_Law.md         ✅ NEW
  @MODE_Multi_Lingual.md        ✅ NEW

  ### MCP Server Integration (Imported)
  @MCP_Entscheidsuche.md        ✅ NEW
  @MCP_Legal_Citations.md       ✅ NEW
  ```

**4.4 Documentation Updates**
- [ ] Update IMPLEMENTATION_STATUS.md:
  - Personas: 3/3 Complete ✅
  - Modes: 3/3 Complete ✅
  - MCP Docs: 2/2 Complete ✅
  - Status: Foundation Phase → 100% Complete ✅

- [ ] Update README.md if needed (should be current)

**4.5 Final Review Checklist**
- [ ] All deliverables meet line count estimates
- [ ] No TODO comments or placeholders
- [ ] Examples are complete and realistic
- [ ] Workflows have proper step counts (5-6 steps)
- [ ] Output templates are comprehensive
- [ ] MCP integration is specific (not generic)

---

## 📊 Progress Tracking

### Completion Metrics

**Overall Progress**:
- Foundation: 60% → 100% (completing 40%)
- Personas: 33% (1/3) → 100% (3/3)
- Modes: 0% (0/3) → 100% (3/3)
- MCP Docs: 0% (0/2) → 100% (2/2)

**Time Investment**:
- Total estimated: 8.5-11 hours
- Optimized (parallel): Can be done in 1-2 work days
- Phase 1: 2-3 hours (modes)
- Phase 2: 4-5 hours (personas)
- Phase 3: 1.5-2 hours (MCP docs)
- Phase 4: 1 hour (validation)

**Deliverables Count**:
- Mode files: 3
- Persona files: 2
- MCP documentation: 2
- Updates: 2 (IMPLEMENTATION_STATUS, BETTERASK)
- **Total**: 9 files

---

## 🎯 Success Criteria

### Technical Completeness
- [ ] All 9 deliverables created
- [ ] Each file meets minimum line count (quality over quantity)
- [ ] No placeholders or TODOs
- [ ] All workflows complete (5-6 steps minimum)

### Swiss Legal Specificity
- [ ] Federal law: ZGB, OR, StGB, StPO, ZPO, BV referenced
- [ ] Cantonal law: All 6 cantons configured
- [ ] Multi-lingual: DE/FR/IT/EN terminology accurate
- [ ] Citations: Proper formatting per language

### Framework Integration
- [ ] Modes properly imported in BETTERASK.md
- [ ] Personas reference modes correctly
- [ ] MCP tools referenced by personas
- [ ] Cross-references validated

### Quality Standards
- [ ] Matches Legal Researcher quality level
- [ ] Professional legal tone maintained
- [ ] Disclaimers present throughout
- [ ] Examples realistic and complete

### Documentation
- [ ] IMPLEMENTATION_STATUS.md updated
- [ ] README.md current
- [ ] All activation triggers documented
- [ ] All workflows testable

---

## 🚀 Execution Strategy

### Parallel Execution Plan

**Day 1 Morning (3-4 hours)**:
- **Parallel Track A**: MODE_Federal_Law.md + MODE_Cantonal_Law.md
- **Parallel Track B**: MODE_Multi_Lingual.md
- Result: All 3 modes complete

**Day 1 Afternoon (4-5 hours)**:
- **Parallel Track A**: PERSONA_Case_Strategist.md
- **Parallel Track B**: PERSONA_Legal_Drafter.md
- Result: All 5 personas complete (including existing Legal Researcher)

**Day 2 Morning (2 hours)**:
- **Parallel Track A**: MCP_Entscheidsuche.md
- **Parallel Track B**: MCP_Legal_Citations.md
- Result: All MCP documentation complete

**Day 2 Mid-morning (1 hour)**:
- Validation & Integration
- Update IMPLEMENTATION_STATUS.md
- Final cross-reference check
- Result: v1.0 Foundation 100% Complete

### Sequential Fallback Plan
If parallel execution not feasible:
1. All modes (6.5 hours)
2. Case Strategist (5 hours)
3. Legal Drafter (5 hours)
4. MCP docs (3 hours)
5. Validation (1 hour)
Total: ~20.5 hours (2.5 work days)

---

## 📝 Quality Checklist Template

Use this for each deliverable:

```markdown
## Quality Checklist: [File Name]

### Structure
- [ ] Follows framework file template
- [ ] All required sections present
- [ ] Markdown formatting correct
- [ ] Line count target met (±10%)

### Content Quality
- [ ] Swiss legal specificity (not generic)
- [ ] Multi-lingual accuracy (DE/FR/IT/EN)
- [ ] Examples realistic and complete
- [ ] Workflows have proper steps (5-6 minimum)

### Integration
- [ ] References other components correctly
- [ ] Activation triggers don't conflict
- [ ] MCP integration specific
- [ ] Terminology consistent with existing files

### Legal Standards
- [ ] Professional legal tone
- [ ] Disclaimers present
- [ ] Citation formats correct
- [ ] Swiss law references accurate

### Validation
- [ ] No TODOs or placeholders
- [ ] All examples complete
- [ ] Cross-references valid
- [ ] Ready for production use
```

---

## 🎓 Learning & Improvement

### Post-Implementation Review

After completion, document:
1. **What Worked Well**: Patterns to reuse
2. **Challenges**: Issues encountered
3. **Time Accuracy**: Compare estimated vs. actual
4. **Quality Issues**: Any gaps or inconsistencies
5. **Future Improvements**: For v1.1+ planning

### Metrics to Track
- Time per deliverable (actual vs. estimated)
- Quality issues found in validation
- Cross-reference errors
- Integration problems
- User feedback (post-launch)

---

## 📞 Next Steps After Completion

### Immediate (Week 1)
1. Beta testing with target users (Swiss lawyers)
2. Citation accuracy validation
3. Multi-lingual consistency verification
4. Documentation review (all languages)

### Short-term (Weeks 2-4)
1. MCP server implementation (Phase 2)
2. Integration testing
3. Performance optimization
4. User documentation (getting-started guides)

### Medium-term (Months 2-3)
1. Additional personas (v1.1)
2. Full cantonal coverage (26 cantons)
3. Local LLM support (Ollama)
4. Feedback collection system

---

**BetterCallClaude v1.0 Implementation Workflow**
**Status**: Ready for execution
**Estimated Completion**: 1-2 work days
**Target**: Foundation Phase 100% Complete

*Generated 2025-01-21 | Last Updated: 2025-01-21*
