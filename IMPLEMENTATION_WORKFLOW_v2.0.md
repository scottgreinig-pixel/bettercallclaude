# BetterCallClaude v2.0 Implementation Workflow

**Generated**: 2025-01-17
**Strategy**: Systematic greenfield implementation leveraging v1.0 specifications
**Duration**: 12 weeks (6 two-week sprints)
**Team**: 2 Full-Stack Developers + Legal Consultant (20%)
**Budget**: CHF 120K

---

## 🎯 Executive Summary

### Project Reality
- **v1.0 State**: 68,000+ lines of complete specifications, zero implementation code
- **Transformation Type**: Greenfield v2.0 implementation (not v1.0 upgrade)
- **Reusable Assets**: Swiss legal methodology, persona patterns, citation system, multi-lingual framework
- **New Development**: 30 commands, 12 personas, 8 MCP servers, 26 canton support

### Success Criteria
- Citation accuracy >95%
- Performance <3s response time
- All 26 Swiss cantons supported
- Multi-lingual (DE/FR/IT/EN) legal reasoning
- Production deployment ready

---

## 📋 Sprint 0: Pre-Implementation Setup (Week -1)

### 🎯 Sprint Goal
Team hired, infrastructure operational, development environment functional

### 👥 Team Hiring

**Developer A - Full-Stack (Python/TypeScript)**
- **Required Skills**:
  - Python 3.11+ (backend development)
  - TypeScript/Node.js (MCP server development)
  - Claude Code / MCP framework experience
  - REST API and web scraping expertise
- **Preferred**: Swiss legal tech background, multi-lingual (DE/FR/IT)
- **Budget**: CHF 30K (12 weeks)
- **Tasks**: Command system, MCP servers, final MCPs

**Developer B - Full-Stack (Python/TypeScript)**
- **Required Skills**:
  - Python 3.11+ (backend development)
  - TypeScript/Node.js (MCP server development)
  - SQLite/PostgreSQL database management
  - Testing frameworks (pytest, jest)
- **Preferred**: Legal tech or compliance system experience
- **Budget**: CHF 30K (12 weeks)
- **Tasks**: Infrastructure, commands, personas, multi-lingual support

**Legal Consultant - Swiss Lawyer (20% capacity)**
- **Required**:
  - Licensed Swiss lawyer (active bar membership)
  - Multi-lingual: Native DE/FR/IT, professional EN
  - BGE precedent and cantonal law expertise
- **Focus**: Citation validation, legal reasoning review, accuracy testing
- **Budget**: CHF 30K (12 weeks, 1 day/week)

### 🏗️ Infrastructure Setup

**1. Repository & Version Control**
```bash
# GitHub Organization Setup
- Create organization: BetterCallClaude
- Repository: bettercallclaude-v2
- Branch protection: main, develop
- PR templates with legal accuracy checklist
- Code owners: @dev-a, @dev-b, @legal-consultant
```

**2. CI/CD Pipeline (GitHub Actions)**
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: [push, pull_request]
jobs:
  backend-tests:
    - pytest with coverage >80%
    - mypy type checking
    - black code formatting
  mcp-servers:
    - jest unit tests
    - TypeScript compilation
    - ESLint validation
  integration:
    - Command + MCP integration tests
    - Legal accuracy smoke tests
```

**3. Development Environment**
```bash
# Python Backend
- Python 3.11+ virtual environment
- pip install -r requirements.txt
- Pre-commit hooks: black, mypy, pytest

# TypeScript MCP Servers
- Node.js 18+ (LTS)
- npm install (MCP SDK, TypeScript)
- ESLint + Prettier configuration

# Claude Code CLI
- Latest Claude Code CLI installed
- MCP server development template
- Local MCP server testing framework
```

**4. Cloud Infrastructure (Staging/Production)**
```yaml
# AWS/Azure/GCP Stack
compute:
  - Development: Local + Docker Compose
  - Staging: Cloud VM (2 vCPU, 8GB RAM)
  - Production: Auto-scaling instances

database:
  - Development: SQLite
  - Staging/Production: PostgreSQL 15+

monitoring:
  - Application logs: CloudWatch/Azure Monitor
  - Performance: New Relic/DataDog
  - Error tracking: Sentry
```

### 📚 Documentation & Onboarding

**Developer Onboarding Guide** (`docs/onboarding/`)
1. **Swiss Legal System 101** (2-hour module)
   - BGE precedent hierarchy
   - Federal vs. cantonal law structure
   - Multi-lingual legal interpretation
   - Citation format standards

2. **v1.0 Specification Review** (4-hour module)
   - Persona behavioral patterns
   - Swiss legal methodology framework
   - Citation system architecture
   - Multi-lingual framework design

3. **v2.0 Architecture Walkthrough** (4-hour module)
   - Command system design
   - MCP server architecture
   - Persona activation mechanism
   - Privacy router and deployment modes

4. **MCP Server Development Tutorial** (hands-on)
   - Build sample MCP server (Hello World)
   - Implement scraping with rate limiting
   - Add caching layer (Redis/SQLite)
   - Testing and deployment

### ✅ Sprint 0 Acceptance Criteria
- [ ] Team hired: 2 developers + legal consultant onboarded
- [ ] GitHub repository with CI/CD pipeline functional
- [ ] Development environment: Sample MCP server running locally
- [ ] Staging environment: Cloud infrastructure deployed
- [ ] Sprint 1 backlog: All stories ready with acceptance criteria
- [ ] Project tracking: Jira/Linear boards configured for 6 sprints

---

## 📦 Sprint 1: Foundation & Core Command System (Weeks 1-2)

### 🎯 Sprint Goal
Command registry operational, 3 commands working, MCP connection framework ready

### 📊 Story Cards (Import-Ready Format)

#### **STORY-1.1: Command Registry System**
```yaml
Title: Implement Core Command Registry System
Type: Feature
Priority: Critical
Story Points: 8
Assignee: Developer A

Description: |
  As a developer, I need a centralized command registry system so that
  commands can be auto-discovered, routed, and executed with proper
  argument validation and error handling.

Acceptance Criteria:
  - [ ] BaseCommand abstract class with metadata (name, category, args)
  - [ ] CommandRegistry with auto-discovery from core/commands/
  - [ ] Command router with argument parsing and validation
  - [ ] Error handling for invalid commands and arguments
  - [ ] Unit tests: >85% coverage

Technical Tasks:
  - [ ] Create core/commands/base.py with BaseCommand ABC
  - [ ] Implement core/commands/registry.py with CommandRegistry class
  - [ ] Build argument parser with type validation (int, str, bool, list)
  - [ ] Add command metadata decorators (@command, @argument)
  - [ ] Write pytest tests for registry and routing

Dependencies: None (foundational)
Blockers: None
Estimated Hours: 16h

Code Reference:
  File: core/commands/base.py
  File: core/commands/registry.py
```

#### **STORY-1.2: /legal:research Command**
```yaml
Title: Implement /legal:research Command (Basic)
Type: Feature
Priority: High
Story Points: 5
Assignee: Developer A

Description: |
  As a Swiss lawyer, I need a /legal:research command to search legal
  sources so that I can find relevant precedents and statutes for my case.

Acceptance Criteria:
  - [ ] Command accepts query string and optional filters (jurisdiction, date)
  - [ ] Returns structured results (case name, citation, summary)
  - [ ] Help text with usage examples
  - [ ] Error handling for empty queries
  - [ ] Integration test with mock legal database

Technical Tasks:
  - [ ] Create core/commands/legal_research.py
  - [ ] Implement execute() method with argument validation
  - [ ] Add result formatting (JSON + human-readable)
  - [ ] Write integration tests with mock data
  - [ ] Document command in docs/commands/legal-research.md

Dependencies: STORY-1.1 (Command Registry)
Blockers: None
Estimated Hours: 10h

Code Reference:
  File: core/commands/legal_research.py
  Example: /legal:research "BGE precedent employment law" --jurisdiction federal
```

#### **STORY-1.3: /legal:help Command**
```yaml
Title: Implement /legal:help Command System
Type: Feature
Priority: High
Story Points: 3
Assignee: Developer A

Description: |
  As a user, I need a /legal:help command to view available commands
  and their usage so that I can discover functionality.

Acceptance Criteria:
  - [ ] Lists all registered commands with descriptions
  - [ ] /legal:help <command> shows detailed usage
  - [ ] Categorizes commands (research, drafting, analysis, etc.)
  - [ ] Examples for each command
  - [ ] Unit tests: >90% coverage

Technical Tasks:
  - [ ] Create core/commands/help.py
  - [ ] Extract metadata from CommandRegistry
  - [ ] Format output with categories and examples
  - [ ] Add command-specific help text
  - [ ] Write pytest tests for help formatting

Dependencies: STORY-1.1 (Command Registry)
Blockers: None
Estimated Hours: 6h

Code Reference:
  File: core/commands/help.py
```

#### **STORY-1.4: SQLite Citation Cache**
```yaml
Title: Set Up SQLite Citation Cache
Type: Infrastructure
Priority: High
Story Points: 5
Assignee: Developer B

Description: |
  As a developer, I need a SQLite-based citation cache so that
  frequently accessed legal citations can be served quickly without
  repeated MCP server calls.

Acceptance Criteria:
  - [ ] SQLite database schema for citations (id, citation, content, timestamp)
  - [ ] Cache hit/miss logic with TTL (24 hours default)
  - [ ] CRUD operations (create, read, update, delete)
  - [ ] Automatic expiration of stale entries
  - [ ] Unit tests: >85% coverage

Technical Tasks:
  - [ ] Create core/cache/citation_cache.py
  - [ ] Design schema: citations table (id, citation_id, content, created_at, ttl)
  - [ ] Implement get(), set(), invalidate() methods
  - [ ] Add TTL-based expiration logic
  - [ ] Write pytest tests with mock SQLite DB

Dependencies: None (foundational)
Blockers: None
Estimated Hours: 10h

Code Reference:
  File: core/cache/citation_cache.py
  Schema: migrations/001_create_citation_cache.sql
```

#### **STORY-1.5: MCP Server Connection Manager**
```yaml
Title: Build MCP Server Connection Manager
Type: Infrastructure
Priority: Critical
Story Points: 8
Assignee: Developer B

Description: |
  As a developer, I need an MCP connection manager to handle
  connections to multiple MCP servers with error handling, retries,
  and connection pooling.

Acceptance Criteria:
  - [ ] MCPConnectionManager class with server registry
  - [ ] Connection pooling for efficiency
  - [ ] Retry logic with exponential backoff
  - [ ] Error handling for server unavailability
  - [ ] Health check endpoints for each server
  - [ ] Unit tests: >85% coverage

Technical Tasks:
  - [ ] Create core/mcp/connection_manager.py
  - [ ] Implement connection pool (max 5 concurrent per server)
  - [ ] Add retry decorator with exponential backoff (3 retries max)
  - [ ] Build health check system (ping every 60s)
  - [ ] Write integration tests with mock MCP servers

Dependencies: None (foundational)
Blockers: None
Estimated Hours: 16h

Code Reference:
  File: core/mcp/connection_manager.py
```

#### **STORY-1.6: Persona Activation Framework**
```yaml
Title: Implement Persona Activation Framework
Type: Feature
Priority: High
Story Points: 5
Assignee: Developer B

Description: |
  As a developer, I need a persona activation framework so that
  commands can automatically activate appropriate legal expert
  personas based on context.

Acceptance Criteria:
  - [ ] PersonaActivator class with persona registry
  - [ ] Auto-activation based on command metadata
  - [ ] Context injection for activated personas
  - [ ] Persona switching mechanism
  - [ ] Unit tests: >85% coverage

Technical Tasks:
  - [ ] Create core/personas/activator.py
  - [ ] Implement persona registry with metadata
  - [ ] Build auto-activation logic (command → personas mapping)
  - [ ] Add context injection system
  - [ ] Write pytest tests for activation logic

Dependencies: STORY-1.1 (Command Registry)
Blockers: None
Estimated Hours: 10h

Code Reference:
  File: core/personas/activator.py
```

### 👥 Parallel Work Strategy (Sprint 1)

**Week 1:**
- **Developer A**: STORY-1.1 (Command Registry) → STORY-1.2 (/legal:research)
- **Developer B**: STORY-1.4 (SQLite Cache) → STORY-1.5 (MCP Connection Manager)
- **Legal Consultant**: Validate BGE citation format specs, provide sample queries

**Week 2:**
- **Developer A**: STORY-1.3 (/legal:help)
- **Developer B**: STORY-1.6 (Persona Activation Framework)
- **Both**: Integration testing (command + MCP framework)
- **Legal Consultant**: Review /legal:research output accuracy

### ✅ Sprint 1 Acceptance Criteria
- [ ] 3 commands operational: /legal:research, /legal:help, /legal:cite
- [ ] Command registry auto-discovers commands from core/commands/
- [ ] MCP connection manager handles 2+ concurrent server connections
- [ ] SQLite citation cache functional with 24-hour TTL
- [ ] Persona activation framework ready for Sprint 3 integration
- [ ] Unit test coverage: >80% across all modules
- [ ] Integration tests passing (command execution end-to-end)

### 📊 Sprint 1 Metrics
- **Velocity Target**: 34 story points
- **Test Coverage**: >80%
- **Code Quality**: All PRs approved by both developers
- **Documentation**: Command documentation complete

---

## 📦 Sprint 2: First MCP Servers & Enhanced Commands (Weeks 3-4)

### 🎯 Sprint Goal
BGE Search MCP + Entscheidsuche MCP operational, 6 commands working, citation accuracy >85%

### 📊 Story Cards (Import-Ready Format)

#### **STORY-2.1: BGE Search MCP Server**
```yaml
Title: Build BGE Search MCP Server (TypeScript)
Type: Feature
Priority: Critical
Story Points: 13
Assignee: Developer A

Description: |
  As a Swiss lawyer, I need an MCP server that scrapes BGE.ch for
  federal court precedents so that I can find authoritative case law.

Acceptance Criteria:
  - [ ] MCP server in TypeScript (mcp-servers/bge-search/)
  - [ ] BGE.ch scraping with rate limiting (max 10 req/min)
  - [ ] Citation extraction and parsing (BGE XX YYYY ZZZZ format)
  - [ ] Relevance ranking algorithm (keyword matching + date weighting)
  - [ ] Caching layer (24-hour TTL, SQLite)
  - [ ] Error handling for scraping failures
  - [ ] Jest unit tests: >85% coverage

Technical Tasks:
  - [ ] Initialize TypeScript project with MCP SDK
  - [ ] Implement BGE.ch scraper (Puppeteer or Cheerio)
  - [ ] Add rate limiting (token bucket algorithm)
  - [ ] Build citation parser (regex for BGE format)
  - [ ] Implement relevance ranking (TF-IDF or simple keyword)
  - [ ] Add SQLite caching with TTL
  - [ ] Write integration tests with mock BGE.ch responses

Dependencies: STORY-1.5 (MCP Connection Manager)
Blockers: BGE.ch structure may change (mitigation: flexible scraper)
Estimated Hours: 26h

Code Reference:
  Directory: mcp-servers/bge-search/
  Files: src/index.ts, src/scraper.ts, src/parser.ts, src/cache.ts
```

#### **STORY-2.2: Entscheidsuche MCP Server**
```yaml
Title: Implement Entscheidsuche MCP Server
Type: Feature
Priority: Critical
Story Points: 10
Assignee: Developer A

Description: |
  As a Swiss lawyer, I need an MCP server for Entscheidsuche.ch
  (Federal Supreme Court database) to search federal court decisions.

Acceptance Criteria:
  - [ ] MCP server in TypeScript (mcp-servers/entscheidsuche/)
  - [ ] Federal court search integration (all court types)
  - [ ] Result normalization (consistent format with BGE Search)
  - [ ] Caching layer (24-hour TTL, SQLite)
  - [ ] Error handling for API failures
  - [ ] Jest unit tests: >85% coverage

Technical Tasks:
  - [ ] Initialize TypeScript project with MCP SDK
  - [ ] Implement Entscheidsuche API client
  - [ ] Build result normalization layer
  - [ ] Add SQLite caching with TTL
  - [ ] Write integration tests with mock API responses

Dependencies: STORY-1.5 (MCP Connection Manager)
Blockers: None
Estimated Hours: 20h

Code Reference:
  Directory: mcp-servers/entscheidsuche/
  Files: src/index.ts, src/api-client.ts, src/normalizer.ts
```

#### **STORY-2.3: /swiss:federal Command**
```yaml
Title: Implement /swiss:federal Command
Type: Feature
Priority: High
Story Points: 5
Assignee: Developer B

Description: |
  As a Swiss lawyer, I need a /swiss:federal command to research
  federal law sources (BGE, federal statutes) in a unified interface.

Acceptance Criteria:
  - [ ] Command integrates BGE Search MCP + Entscheidsuche MCP
  - [ ] Accepts query + filters (date range, court type)
  - [ ] Returns ranked results from both MCPs
  - [ ] Deduplicates results across sources
  - [ ] Help text with examples

Technical Tasks:
  - [ ] Create core/commands/swiss_federal.py
  - [ ] Integrate MCPConnectionManager for BGE + Entscheidsuche
  - [ ] Implement result merging and deduplication
  - [ ] Add ranking algorithm (combine scores from both MCPs)
  - [ ] Write integration tests with mock MCP responses

Dependencies: STORY-2.1 (BGE Search), STORY-2.2 (Entscheidsuche)
Blockers: None
Estimated Hours: 10h

Code Reference:
  File: core/commands/swiss_federal.py
  Example: /swiss:federal "employment law termination" --date-range 2020-2024
```

#### **STORY-2.4: /swiss:precedent Command**
```yaml
Title: Implement /swiss:precedent Command
Type: Feature
Priority: High
Story Points: 5
Assignee: Developer B

Description: |
  As a Swiss lawyer, I need a /swiss:precedent command specifically
  for BGE precedent search with advanced filtering.

Acceptance Criteria:
  - [ ] Command integrates BGE Search MCP only
  - [ ] Advanced filters (legal area, court chamber, outcome)
  - [ ] Citation-based search (find cases citing specific BGE)
  - [ ] Precedent hierarchy visualization
  - [ ] Help text with examples

Technical Tasks:
  - [ ] Create core/commands/swiss_precedent.py
  - [ ] Integrate BGE Search MCP
  - [ ] Implement advanced filtering logic
  - [ ] Add citation graph functionality
  - [ ] Write integration tests

Dependencies: STORY-2.1 (BGE Search)
Blockers: None
Estimated Hours: 10h

Code Reference:
  File: core/commands/swiss_precedent.py
```

#### **STORY-2.5: /doc:analyze Command**
```yaml
Title: Implement /doc:analyze Command
Type: Feature
Priority: Medium
Story Points: 5
Assignee: Developer B

Description: |
  As a Swiss lawyer, I need a /doc:analyze command to analyze legal
  documents for citations, legal issues, and jurisdictional scope.

Acceptance Criteria:
  - [ ] Accepts file path or text input
  - [ ] Extracts citations (BGE, cantonal, statutes)
  - [ ] Identifies legal issues (keywords: contract, tort, etc.)
  - [ ] Detects jurisdiction (federal, cantonal, multi-lingual)
  - [ ] Returns structured analysis report

Technical Tasks:
  - [ ] Create core/commands/doc_analyze.py
  - [ ] Implement citation extraction (regex patterns)
  - [ ] Build legal issue classifier (keyword matching)
  - [ ] Add jurisdiction detection logic
  - [ ] Write unit tests with sample documents

Dependencies: None
Blockers: None
Estimated Hours: 10h

Code Reference:
  File: core/commands/doc_analyze.py
```

#### **STORY-2.6: Enhanced /legal:cite Command**
```yaml
Title: Enhance /legal:cite with MCP Integration
Type: Enhancement
Priority: Medium
Story Points: 3
Assignee: Developer B

Description: |
  As a Swiss lawyer, I need /legal:cite to verify citations using
  BGE Search MCP so that I can confirm citation accuracy.

Acceptance Criteria:
  - [ ] Accepts citation string (e.g., "BGE 147 V 321")
  - [ ] Queries BGE Search MCP for verification
  - [ ] Returns citation validity + full case details if found
  - [ ] Suggests corrections for malformed citations
  - [ ] Unit tests: >85% coverage

Technical Tasks:
  - [ ] Enhance core/commands/legal_cite.py
  - [ ] Integrate BGE Search MCP for verification
  - [ ] Add citation correction logic (fuzzy matching)
  - [ ] Write integration tests

Dependencies: STORY-2.1 (BGE Search)
Blockers: None
Estimated Hours: 6h

Code Reference:
  File: core/commands/legal_cite.py (enhancement)
```

### 👥 Parallel Work Strategy (Sprint 2)

**Week 3:**
- **Developer A**: STORY-2.1 (BGE Search MCP) - high complexity, full focus
- **Developer B**: STORY-2.3 (/swiss:federal) + STORY-2.4 (/swiss:precedent) prep
- **Legal Consultant**: Test BGE Search accuracy (50 sample citations)

**Week 4:**
- **Developer A**: STORY-2.2 (Entscheidsuche MCP)
- **Developer B**: STORY-2.5 (/doc:analyze) + STORY-2.6 (Enhanced /legal:cite)
- **Both**: Integration testing (commands + MCPs)
- **Legal Consultant**: Validate federal law prioritization, provide cantonal law examples

### ✅ Sprint 2 Acceptance Criteria
- [ ] 2 MCP servers deployed: BGE Search + Entscheidsuche
- [ ] 6 commands operational (3 new: /swiss:federal, /swiss:precedent, /doc:analyze)
- [ ] Citation accuracy >85% on federal cases (legal consultant validation)
- [ ] BGE Search response time <3 seconds average
- [ ] Entscheidsuche handles all federal court types
- [ ] Integration tests passing (all command + MCP combinations)
- [ ] MCP server monitoring dashboard functional

### 📊 Sprint 2 Metrics
- **Velocity Target**: 41 story points
- **Citation Accuracy**: >85% (target: 50 test cases)
- **Performance**: <3s response time (BGE Search)
- **MCP Uptime**: >99% (staging environment)

---

## 🔄 Critical Path & Dependency Map

```
Sprint 0: Team + Infrastructure
    ↓
Sprint 1: Command System + MCP Framework
    ↓
Sprint 2: BGE Search MCP + Entscheidsuche MCP
    ├─→ Citation accuracy baseline established
    ├─→ MCP integration patterns proven
    └─→ Performance benchmarks set
    ↓
Sprint 3: Persona System + Cantonal Courts MCP
    ├─→ Persona patterns from v1.0 implemented
    ├─→ 3 cantons (ZH, BE, GE) operational
    └─→ 12 commands working (50% complete)
    ↓
Sprint 4: Multi-lingual + Additional MCPs
    ├─→ DE/FR/IT/EN legal reasoning
    ├─→ 6 MCP servers (75% complete)
    └─→ 20 commands (67% complete)
    ↓
Sprint 5: Complete Feature Set
    ├─→ All 30 commands
    ├─→ All 12 personas
    ├─→ All 8 MCPs
    └─→ 26 cantons supported
    ↓
Sprint 6: QA + Launch
    ├─→ Citation accuracy >95%
    ├─→ Performance <3s
    ├─→ Security audit passed
    └─→ Production deployment ready
```

### 🚨 Critical Blockers to Watch

**Sprint 2 Blocker: BGE.ch Scraping Stability**
- **Risk**: BGE.ch structure changes break scraper
- **Impact**: Citation accuracy falls below 85%
- **Mitigation**:
  - Build flexible scraper with multiple parsing strategies
  - Legal consultant validates 10% of citations weekly
  - Fallback to manual citation verification if <85%
- **Owner**: Developer A
- **Status**: Monitor Sprint 2 Week 1

**Sprint 3-5 Blocker: Cantonal Court Access**
- **Risk**: Some cantons restrict web scraping or have no public API
- **Impact**: Cannot achieve 26/26 canton coverage
- **Mitigation**:
  - Start with 6 known-accessible cantons (ZH, BE, GE, BS, VD, TI)
  - Legal consultant identifies alternative data sources
  - Build generic scraper framework for flexibility
- **Owner**: Developer A + Legal Consultant
- **Status**: Monitor Sprint 3 Week 1

**Sprint 1-6 Ongoing: Legal Consultant Availability**
- **Risk**: Legal consultant unavailable for critical validation
- **Impact**: Delays in accuracy testing, persona review
- **Mitigation**:
  - Schedule weekly 4-hour blocks (Fridays)
  - Batch validation tasks for efficient use of time
  - Build automated accuracy tests to reduce manual validation
- **Owner**: Project Manager
- **Status**: Monitor weekly

---

## ⚠️ Risk Register & Mitigation Strategies

### High-Risk Items

**RISK-001: Citation Accuracy Below 95% Target**
- **Probability**: Medium (40%)
- **Impact**: High (blocker for launch)
- **Mitigation**:
  - Sprint 2: Allocate extra 8 hours for BGE scraping tuning
  - Sprint 2-6: Legal consultant validates 10% citations weekly
  - Sprint 6: Build 1000-case test suite for validation
  - Fallback: Manual citation verification system
- **Owner**: Developer A + Legal Consultant
- **Review Cadence**: Weekly

**RISK-002: MCP Performance Issues (>3s response time)**
- **Probability**: Medium (35%)
- **Impact**: Medium (user experience degradation)
- **Mitigation**:
  - Sprint 1: Implement aggressive caching (24-hour TTL)
  - Sprint 2: Add rate limiting from day 1
  - Sprint 6: Performance testing with 100 concurrent requests
  - Optimization: CDN for static legal documents
- **Owner**: Developer B
- **Review Cadence**: Sprint 2, 4, 6

### Medium-Risk Items

**RISK-003: Team Ramp-Up Time**
- **Probability**: Medium (30%)
- **Impact**: Medium (Sprint 1-2 velocity reduction)
- **Mitigation**:
  - Sprint 0: Dedicated 2-day onboarding
  - Sprint 1: Pair programming for first week
  - Legal consultant available for questions (4h/week)
- **Owner**: Project Manager
- **Review Cadence**: Sprint 0, 1

**RISK-004: Cantonal Court Data Inaccessibility**
- **Probability**: Medium (25%)
- **Impact**: Medium (26 canton coverage at risk)
- **Mitigation**:
  - Sprint 3: Start with 6 known-accessible cantons
  - Sprint 4-5: Legal consultant identifies alternatives
  - Build generic scraper framework for flexibility
  - Fallback: Partial canton coverage (prioritize high-volume cantons)
- **Owner**: Developer A + Legal Consultant
- **Review Cadence**: Sprint 3, 4, 5

### Low-Risk Items

**RISK-005: Multi-lingual Accuracy Issues**
- **Probability**: Low (15%)
- **Impact**: Low (specific language pairs affected)
- **Mitigation**:
  - Sprint 4: Legal consultant tests DE→FR, IT→EN translations
  - Sprint 5: Cross-language citation validation
  - Fallback: English-only mode for specific legal areas
- **Owner**: Developer B + Legal Consultant
- **Review Cadence**: Sprint 4, 5

---

## 📈 Success Metrics & KPIs

### Sprint-Level Metrics

| Sprint | Story Points | Commands | MCPs | Personas | Citation Accuracy | Performance |
|--------|-------------|----------|------|----------|-------------------|-------------|
| Sprint 1 | 34 | 3 | 0 | 0 | N/A | N/A |
| Sprint 2 | 41 | 6 | 2 | 0 | >85% | <3s |
| Sprint 3 | 38 | 12 | 3 (partial) | 6 | >88% | <3s |
| Sprint 4 | 40 | 20 | 6 | 6 | >92% | <3s |
| Sprint 5 | 42 | 30 | 8 | 12 | >95% | <3s |
| Sprint 6 | 35 | 30 | 8 | 12 | >95% | <2.5s |

### Quality Gates

**Code Quality (Continuous)**
- Unit test coverage: >80% (Sprint 1-6)
- Integration test coverage: >70% (Sprint 2-6)
- Code review: 100% PRs approved by 2 developers
- Static analysis: No critical issues (mypy, ESLint)

**Legal Accuracy (Sprint 2-6)**
- Citation verification: >95% accuracy (1000 test cases by Sprint 6)
- Persona authenticity: Legal consultant sign-off each sprint
- Multi-lingual consistency: <5% variance across languages

**Performance (Sprint 2, 6)**
- Response time: <3s average (Sprint 2-5), <2.5s (Sprint 6)
- Concurrent users: 100 simultaneous requests (Sprint 6)
- MCP uptime: >99% (staging/production)

**Security (Sprint 6)**
- OWASP Top 10: No critical vulnerabilities
- Data privacy: Swiss legal data protection compliance
- Penetration testing: External security audit passed

---

## 💰 Budget Allocation & Tracking

### Total Budget: CHF 120K

**Personnel (CHF 90K)**
- Developer A: CHF 30K (12 weeks @ CHF 2.5K/week)
- Developer B: CHF 30K (12 weeks @ CHF 2.5K/week)
- Legal Consultant: CHF 30K (12 weeks @ 20% capacity)

**Infrastructure (CHF 15K)**
- Cloud hosting (AWS/Azure/GCP): CHF 8K
  - Staging: CHF 2K (12 weeks @ CHF 167/week)
  - Production: CHF 6K (12 weeks @ CHF 500/week)
- CI/CD tools (GitHub Actions, monitoring): CHF 3K
- Development tools (licenses, APIs): CHF 2K
- Third-party data sources: CHF 2K

**Contingency (CHF 15K)**
- Additional legal consultant hours: CHF 5K
- Performance optimization tools: CHF 3K
- External security audit: CHF 5K
- Miscellaneous (buffer): CHF 2K

### Burn Rate Tracking

| Sprint | Personnel | Infrastructure | Contingency | Total | Cumulative |
|--------|-----------|---------------|-------------|-------|------------|
| Sprint 0 | CHF 5K | CHF 2K | CHF 0 | CHF 7K | CHF 7K |
| Sprint 1 | CHF 15K | CHF 2.5K | CHF 0 | CHF 17.5K | CHF 24.5K |
| Sprint 2 | CHF 15K | CHF 2.5K | CHF 2K | CHF 19.5K | CHF 44K |
| Sprint 3 | CHF 15K | CHF 2.5K | CHF 1K | CHF 18.5K | CHF 62.5K |
| Sprint 4 | CHF 15K | CHF 2.5K | CHF 2K | CHF 19.5K | CHF 82K |
| Sprint 5 | CHF 15K | CHF 2.5K | CHF 3K | CHF 20.5K | CHF 102.5K |
| Sprint 6 | CHF 15K | CHF 2.5K | CHF 7K | CHF 24.5K | CHF 127K |

**Note**: Budget includes CHF 7K contingency reserve. Target: Stay within CHF 120K.

---

## 🎯 Next Steps for Implementation

### Immediate Actions (This Week)
1. **Review & Validate**: Share this workflow with stakeholders for feedback
2. **Recruit Team**: Post job listings for 2 full-stack developers + legal consultant
3. **Provision Infrastructure**: Set up GitHub organization + cloud accounts
4. **Prepare Sprint 0**: Create onboarding materials and development environment guide

### Sprint 0 Kickoff (Week -1)
1. **Team Onboarding**: 2-day intensive (Swiss legal system + v2.0 architecture)
2. **Environment Setup**: Configure CI/CD, deploy staging infrastructure
3. **Sprint 1 Planning**: Groom backlog, finalize story point estimates
4. **Tooling Setup**: Jira/Linear boards, Slack/Teams channels, documentation wiki

### Sprint 1 Launch (Week 1)
1. **Daily Standups**: 15-min sync (blockers, progress, help needed)
2. **Pair Programming**: Developer A + B for command registry (first 2 days)
3. **Legal Consultant Sync**: Friday 4-hour session (BGE citation validation)
4. **End-of-Sprint Review**: Demo 3 working commands to stakeholders

---

## 📚 Appendix: Story Card Templates

### Jira CSV Import Template
```csv
Summary,Issue Type,Priority,Story Points,Assignee,Description,Acceptance Criteria,Labels,Sprint
"Implement Core Command Registry System",Story,High,8,Developer A,"As a developer, I need a centralized command registry...","- [ ] BaseCommand abstract class\n- [ ] CommandRegistry auto-discovery","backend,foundation",Sprint 1
```

### Linear Import Template (JSON)
```json
{
  "title": "Implement Core Command Registry System",
  "description": "As a developer, I need a centralized command registry...",
  "priority": 1,
  "estimate": 8,
  "teamId": "bettercallclaude-dev",
  "cycleId": "sprint-1",
  "labels": ["backend", "foundation"],
  "assigneeId": "developer-a"
}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-17
**Owner**: Federico Cesconi
**Status**: Ready for Team Review
