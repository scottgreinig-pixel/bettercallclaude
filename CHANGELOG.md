# Changelog

All notable changes to BetterCallClaude will be documented in this file.

---

## [4.1.3] - 2026-04-06

### Changed
- **Architecture refactoring**: Migrated domain methodology from 13 commands into 14 skills
- Commands now serve as thin entry points (5-13 lines) that delegate to skills
- Established single source of truth: skills contain methodology, commands provide slash-command interfaces

### Added
- **4 new skills**: `swiss-legal-translation`, `swiss-document-analysis`, `output-summarization`, `legal-query-refinement`
- Skills now total 14 (up from 10)

### Unchanged
- 6 infrastructure commands remain full-featured: `legal`, `setup`, `help`, `workflow`, `briefing`, `version`
- All 20 agents unchanged
- All 6 MCP servers unchanged

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.0.1] - 2026-03-11

### Fixed
- MCP servers now appear in Cowork Desktop after marketplace installation
- Switched 5 servers from STDIO to HTTP transport (`mcp.bettercallclaude.ch`)
- Cowork Desktop sandboxed VM environment cannot run STDIO-based MCP servers

### Changed
- `bettercallclaude/.mcp.json`: 5 servers use HTTP, ollama remains STDIO for privacy
- Version bumped from 4.0.0 to 4.0.1 across 5 configuration files

### Architecture
- **HTTP transport** (5 servers): `entscheidsuche`, `bge-search`, `legal-citations`, `fedlex-sparql`, `onlinekommentar`
- **STDIO transport** (1 server): `ollama` — must run locally for attorney-client privilege detection (Art. 321 StGB / Anwaltsgeheimnis)

---

## [4.0.0] - 2026-03-03

### Added
- HTTP MCP service deployment at `mcp.bettercallclaude.ch` (Railway)
- Cowork Desktop installation guide with visual screenshots (`docs/cowork-setup.md`)
- README badges for version, license, platform, website, MCP support

### Changed
- HTTP-first MCP transport architecture for zero-config Cowork installation
- README rewritten with Cowork-first messaging (534→219 lines)
- ESLint migrated to v9 flat config
- Repository consolidation: single source of truth in `bettercallclaude/`

---

## [3.0.0] - 2026-02-14

### Repository Consolidation

BetterCallClaude is now a single unified repository for both Claude Code CLI and Cowork Desktop.

#### Changed
- **Repository structure**: Plugin files hoisted from `plugins/bettercallclaude/` to repo root
- **Repository name**: Renamed from `BetterCallClaude_Marketplace` to `bettercallclaude`
- **Plugin manifest**: Replaced `marketplace.json` with standard `plugin.json` at `.claude-plugin/`
- **Version**: Bumped to 3.0.0 to reflect major structural change

#### Added
- **TypeScript source**: MCP server source code imported to `mcp-servers-src/` from original repo
- **Build system**: `scripts/build-servers.sh` for esbuild bundling from TypeScript source
- **Package script**: `scripts/package-plugin.sh` for creating distributable plugin zips
- **CI/CD**: GitHub Actions workflows for testing and releases
- **Documentation**: Imported `docs/` and `CHANGELOG.md` from original repo

#### Removed
- **Nested plugin structure**: No more `plugins/bettercallclaude/` subdirectory
- **Marketplace config**: `marketplace.json` replaced by `plugin.json`

#### Migration
- Existing Cowork installs via marketplace continue to work (GitHub auto-redirects old URLs)
- CLI users: `claude plugin add fedec65/bettercallclaude`
- No changes to commands, agents, skills, or MCP servers

---

## [2.2.1] - 2026-01-17

### 🪟 Windows Compatibility: Command Syntax Migration

This release fixes Windows filesystem compatibility by migrating all slash command filenames from colon (`:`) to hyphen (`-`) format.

### ⚠️ BREAKING CHANGE: Command Syntax

**All slash commands now use hyphens instead of colons:**

| Old Syntax (v2.2.0) | New Syntax (v2.2.1) |
|---------------------|---------------------|
| `/legal:research` | `/legal-research` |
| `/legal:strategy` | `/legal-strategy` |
| `/legal:draft` | `/legal-draft` |
| `/legal:federal` | `/legal-federal` |
| `/legal:cantonal` | `/legal-cantonal` |
| `/legal:cite` | `/legal-cite` |
| `/legal:help` | `/legal-help` |
| `/legal:version` | `/legal-version` |
| `/legal:routing` | `/legal-routing` |
| `/agent:researcher` | `/agent-researcher` |
| `/agent:strategist` | `/agent-strategist` |
| `/agent:drafter` | `/agent-drafter` |
| `/agent:orchestrator` | `/agent-orchestrator` |
| `/agent:compliance` | `/agent-compliance` |
| `/agent:risk` | `/agent-risk` |
| `/agent:procedure` | `/agent-procedure` |
| `/agent:fiscal` | `/agent-fiscal` |
| `/agent:corporate` | `/agent-corporate` |
| `/agent:realestate` | `/agent-realestate` |
| `/agent:translator` | `/agent-translator` |
| `/agent:cantonal` | `/agent-cantonal` |
| `/agent:citation` | `/agent-citation` |
| `/agent:data-protection` | `/agent-data-protection` |
| `/doc:analyze` | `/doc-analyze` |
| `/swiss:federal` | `/swiss-federal` |
| `/swiss:precedent` | `/swiss-precedent` |

### Why This Change?

**Windows Filesystem Restriction**: Windows reserves the colon (`:`) character for drive letter designations (e.g., `C:`). Files containing colons cannot be created or checked out on Windows systems.

**CI/CD Impact**: GitHub Actions Windows runners (`windows-2022`) failed with Git exit code 128:
```
error: invalid path '.claude/commands/agent:cantonal.md'
```

### Changed

- **26 Command Files Renamed**: All `.claude/commands/*.md` files migrated from colon to hyphen format
- **Documentation Updated**: CLAUDE.md, README.md, BETTERASK.md, command-reference.md, AGENT_ARCHITECTURE.md
- **Windows CI Restored**: PowerShell installer tests now pass on Windows

### Migration Guide

**Update your workflows and scripts:**

```bash
# Old (v2.2.0)
/legal:research "Art. 97 OR"
/agent:researcher @case.md

# New (v2.2.1)
/legal-research "Art. 97 OR"
/agent-researcher @case.md
```

**Search and replace in your code:**
- Replace `/legal:` with `/legal-`
- Replace `/agent:` with `/agent-`
- Replace `/doc:` with `/doc-`
- Replace `/swiss:` with `/swiss-`
- Replace `/case:` with `/case-`

### Backward Compatibility

⚠️ **Not Backward Compatible**: Old colon-based commands will not work after this update.

Users must update their workflows, scripts, and muscle memory to use the new hyphen-based syntax.

---

## [2.0.1] - 2025-12-28

### 🏛️ New MCP Server: Fedlex SPARQL

This release introduces the `fedlex-sparql` MCP server for accessing Swiss Federal Legislation through the LINDAS (Linked Data Service) SPARQL endpoint.

### Added

#### Fedlex SPARQL MCP Server
- **New MCP Server**: `fedlex-sparql` for Swiss Federal Law access via SPARQL
- **LINDAS Integration**: Direct connection to `https://ld.admin.ch/query` endpoint
- **ELI Ontology Support**: European Legislation Identifier standard compliance

#### Five New Tools
- **`lookup_statute`**: Find federal legislation by SR/RS number or abbreviation
  - SR number lookup (e.g., "220" for OR/CO)
  - Abbreviation lookup (e.g., "OR", "ZGB", "StGB")
  - Multi-lingual support (DE/FR/IT/RM)

- **`get_article`**: Retrieve specific articles from legislation
  - Article text extraction
  - Language-specific retrieval
  - Article listing for a statute

- **`search_legislation`**: Full-text search across federal law
  - Title and content search
  - Domain filtering (9 legal domains)
  - Recently modified acts
  - Pagination support

- **`find_related`**: Discover legislative relationships
  - Amending acts (eli:amends)
  - Cited legislation (eli:cites)
  - Same-domain legislation
  - Comprehensive relationship mapping

- **`get_metadata`**: Retrieve comprehensive legislation metadata
  - Dates (entry in force, publication, modification)
  - Document type and classification
  - Available languages
  - Legal status (in force, repealed)

#### Query Infrastructure
- **SPARQL Query Builders**: Type-safe query construction
  - Prefix management (RDF, ELI, Fedlex namespaces)
  - Injection-safe escaping
  - Language filter construction
  - Multi-lingual value extraction

- **Legal Domain Classification**: All 9 SR classification domains
  - 1: Staat - Volk - Behörden / État - Peuple - Autorités
  - 2: Privatrecht - Zivilrechtspflege - Vollstreckung
  - 3: Strafrecht - Strafrechtspflege - Strafvollzug
  - 4: Schule - Wissenschaft - Kultur
  - 5: Landesverteidigung
  - 6: Finanzen
  - 7: Öffentliche Werke - Energie - Verkehr
  - 8: Gesundheit - Arbeit - Soziale Sicherheit
  - 9: Wirtschaft - Technische Zusammenarbeit

#### Test Suite
- **Unit Tests**: Comprehensive coverage for SPARQL client and query builders
  - `sparql-client.test.ts`: Escaping, language filters, HTTP execution
  - `queries.test.ts`: All query builders, prefix handling, security tests
- **Security Tests**: SPARQL injection prevention validation

#### Type System
- **Legislation Types**: Full TypeScript definitions
  - `LegislationInfo`: Core statute information
  - `ArticleInfo`: Article content and metadata
  - `RelatedLegislation`: Relationship data
  - `LegislationMetadata`: Comprehensive metadata
  - `SearchResult` and `SearchFilters`: Search functionality
  - `SparqlBindingValue` and `SparqlResponse`: SPARQL response handling

### Technical Details

#### SPARQL Endpoint
- **URL**: `https://ld.admin.ch/query`
- **Protocol**: HTTP POST with SPARQL query body
- **Response**: `application/sparql-results+json`

#### Namespaces Used
```sparql
PREFIX eli: <http://data.europa.eu/eli/ontology#>
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX fedlex: <https://fedlex.data.admin.ch/vocabulary/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
```

### Changed
- **Version**: Updated to 2.0.1 across all configuration files
- **Workspaces**: Added `fedlex-sparql` to npm workspaces in `mcp-servers/package.json`

### Files Added
```
mcp-servers/fedlex-sparql/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              # MCP server entry point
│   ├── sparql-client.ts      # LINDAS HTTP client
│   ├── types/
│   │   └── legislation.ts    # TypeScript interfaces
│   └── queries/
│       ├── index.ts          # Barrel exports
│       ├── prefixes.ts       # SPARQL namespace prefixes
│       ├── lookup.ts         # Statute lookup queries
│       ├── articles.ts       # Article retrieval queries
│       ├── search.ts         # Search queries
│       ├── related.ts        # Relationship queries
│       └── metadata.ts       # Metadata queries
└── tests/
    ├── sparql-client.test.ts # Client unit tests
    └── queries.test.ts       # Query builder tests
```

### Backward Compatibility
- **Fully Backward Compatible**: No breaking changes from v2.0.0
- **Additive Only**: New MCP server extends existing capabilities

---

## [2.0.0] - 2024-12-15

### 🚀 Major Release: PipelineBuilder API & Dynamic Agent Registry

This release introduces the powerful PipelineBuilder API for custom multi-agent workflows, dynamic agent discovery, and parallel execution capabilities.

### Added

#### PipelineBuilder API
- **Fluent Builder Pattern**: Create custom multi-agent workflows with chainable methods
  - `add_step()` - Add sequential pipeline steps
  - `add_parallel_group()` - Run agents concurrently
  - `add_conditional_step()` - Branch based on runtime conditions
  - `add_router()` - Dynamic routing to different agents
  - `with_timeout()` - Set step-level timeouts
  - `with_checkpoint()` - Add checkpoint markers
  - `with_input_mapping()` - Configure data flow between steps
  - `build()` - Compile pipeline for execution

#### Dynamic Agent Registry
- **Auto-Discovery**: Automatically discovers all agents from:
  - Python agent classes in `src/agents/`
  - Command files in `.claude/commands/agent:*.md`
- **Unified Metadata**: Consistent `AgentDescriptor` for all 14 agent types
- **CommandAgentAdapter**: Seamlessly integrates command-file agents with Python orchestration

#### Parallel Execution
- **Concurrent Agent Execution**: Run independent agents simultaneously
- **Merge Strategies**: `all`, `first_success`, `majority` result aggregation
- **Performance Gains**: Significant speed improvements for complex pipelines

#### Conditional Routing
- **Runtime Branching**: Execute different paths based on context
- **Router Steps**: Dynamic agent selection based on intermediate results
- **Condition Functions**: Lambda-based decision logic

#### Pipeline Execution
- **PipelineExecutor**: Execute compiled pipelines with full context management
- **PipelineExecutionResult**: Detailed execution results with timing and status
- **Checkpoint Aggregation**: Collect checkpoints across all pipeline steps

#### Convenience Functions
- `create_research_pipeline()` - Pre-built research workflow
- `create_full_case_pipeline()` - Complete case analysis workflow

#### New Exports
```python
from src.agents import (
    PipelineBuilder,
    PipelineExecutor,
    PipelineStep,
    PipelineExecutionResult,
    Pipeline,
    ConditionalStep,
    ParallelGroup,
    RouterStep,
    StepType,
    create_research_pipeline,
    create_full_case_pipeline,
)
```

### Changed
- **Agent Command Naming**: Standardized to colon-separated format (`agent:*.md`)
- **Registry Architecture**: Unified discovery for Python and command-based agents
- **Documentation**: Comprehensive update to README.md with v2.0.0 features

### Fixed
- E2E test assertions for `pipeline_id` (now UUID-based)
- Test compatibility with Vitest migration for MCP servers

### Backward Compatibility
- **Fully Backward Compatible**: All v1.x orchestrator code continues to work unchanged
- **14 Agents Supported**: 3 Python agents + 11 Command-based agents

---

## [1.5.0] - 2025-01-24

### Database Layer & Performance Infrastructure

This release adds enterprise-grade database infrastructure, comprehensive test coverage, and performance benchmarking.

### Added

#### Database Infrastructure
- **Database Client** with connection pooling and transaction support
  - SQLite support for development and embedded deployment
  - PostgreSQL support for production environments
  - Automatic connection management and cleanup
  - Transaction-safe batch operations

- **Migration System** for idempotent schema evolution
  - Automatic schema versioning
  - Rollback support
  - Development and production migration paths

- **Repository Pattern** for data access abstraction
  - `BGERepository`: CRUD operations for federal court decisions
  - `CantonalRepository`: Canton-specific decision management
  - `CacheRepository`: High-performance caching layer
  - `SearchRepository`: Search analytics and query logging

#### Test Infrastructure (209 tests, 100% pass rate)

- **Unit Tests** (65 tests, 90%+ coverage)
  - Repository method validation
  - Type safety verification
  - Error handling scenarios

- **Integration Tests** (28 tests)
  - Cross-repository workflows
  - Data persistence validation
  - Connection lifecycle management
  - Database recovery scenarios
  - Concurrent access patterns

- **Performance Benchmarks** (25 tests) ✨ NEW
  - **Insertion Performance**: 7 tests covering bulk inserts, cache writes, mixed operations
  - **Query Performance**: 11 tests for lookups, searches, aggregations
  - **Concurrency Performance**: 7 tests for concurrent reads, write contention, connection lifecycle

#### Performance Metrics Established
- **Insertion Rate**: 20-50 records/second (SQLite)
- **Query Rate**: 50-100 queries/second (indexed lookups)
- **Cache Operations**: 100 operations/second
- **Connection Overhead**: 10-20ms per lifecycle
- **Test Suite Execution**: 1.363 seconds for 209 tests

#### Configuration & Tooling
- **TypeScript Configuration**
  - Test-specific tsconfig with proper module resolution
  - Out-of-scope file handling with moduleNameMapper
  - Modern Jest transform configuration

- **Enhanced .gitignore**
  - Comprehensive Python, Node.js, and database exclusions
  - IDE and OS-specific patterns
  - Build output and test artifact management

### Technical Improvements

#### Date Handling
- Fixed SQLite date type binding (Date objects → ISO string format)
- Consistent date formatting across all repositories
- Proper timezone handling for Swiss legal requirements

#### Interface Correctness
- Fixed SearchRepository interface field names
- Added required `id` field to all query operations
- Type-safe query parameter validation

#### Test Reliability
- Timestamp-based unique identifiers prevent test collisions
- Proper database cleanup in afterEach hooks
- File-based SQLite for realistic persistence testing
- Sequential test execution with --runInBand

### Documentation

#### New Documentation Files
- `SPRINT3_PHASE1_COMPLETE.md`: Complete phase summary with technical details
- `INTEGRATION_TEST_RESULTS.md`: Integration test findings and fixes
- Performance benchmark documentation with metrics and baselines

#### Updated Documentation
- `IMPLEMENTATION_STATUS.md`: Updated to reflect 100% Phase 1 completion
- Test coverage reports and performance baselines
- Database schema documentation

### Breaking Changes

⚠️ **Database Schema**: This release introduces new database tables and requires migration.

```bash
# Run migrations before upgrading
npm run migrate
```

⚠️ **Repository API**: New repository pattern replaces direct database access.

```typescript
// OLD (v1.x)
const db = await getDatabase();
const result = await db.query('SELECT * FROM decisions');

// NEW (v2.0)
const client = new DatabaseClient(config);
await client.connect();
const repo = new BGERepository(client);
const result = await repo.findAll();
```

### Migration Guide

#### From v1.x to v2.0

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Run Database Migrations**
   ```bash
   cd mcp-servers/shared
   npm run migrate
   ```

3. **Update Code to Use Repository Pattern**
   ```typescript
   import { DatabaseClient } from './database/client';
   import { BGERepository } from './database/repositories/bge-repository';

   const config = { type: 'sqlite', filename: 'decisions.db' };
   const client = new DatabaseClient(config);
   await client.connect();
   await client.migrate();

   const bgeRepo = new BGERepository(client);
   const decisions = await bgeRepo.findByCitation('BGE 150 I 200');
   ```

4. **Run Tests to Verify**
   ```bash
   npm test
   ```

### Performance Benchmarks

#### Insertion Performance
```
Bulk Insert (100 records): ~2-5 seconds
Per Record: 20-50ms
Cache Writes (100 entries): <3 seconds
Mixed Operations (100 ops): <5 seconds
```

#### Query Performance
```
Citation Lookups (100 queries): <2 seconds (<20ms each)
Cache Lookups (100 queries): <1 second (<10ms each)
Full-Text Search (50 queries): <10 seconds
Count Operations (100 queries): <2 seconds
Cache Hit Rate: >90%
```

#### Concurrency Performance
```
Concurrent Reads (5 connections × 100 reads): <10 seconds
Sequential Writes (100 records): <5 seconds
Connection Lifecycle (50 cycles): <5 seconds (<100ms/cycle)
```

### Known Issues

- **SQLite Write Serialization**: Concurrent writes are serialized (SQLite limitation)
- **ts-jest Warning**: `isolatedModules` deprecation warning (non-blocking)

### Dependencies

#### New Dependencies
- `better-sqlite3`: ^11.8.1 (SQLite driver)
- `pg`: ^8.13.1 (PostgreSQL driver)
- `@types/better-sqlite3`: ^7.6.12
- `@types/pg`: ^8.11.10

#### Updated Dependencies
- TypeScript to latest stable
- Jest configuration modernized

---

## [1.0.0-alpha] - 2025-01-12

### Initial Release

#### Core Features
- Three expert legal personas (Legal Researcher, Case Strategist, Legal Drafter)
- Swiss law modes (Federal, Cantonal, Multi-Lingual)
- MCP server integration (entscheidsuche, legal-citations)
- Multi-jurisdictional Swiss law support (6 cantons)
- Legal symbol system and citation formatting

#### Infrastructure
- Basic MCP server architecture
- TypeScript-based court decision search
- Citation extraction and verification
- Configuration system

---

## Version Comparison: v1.0 → v2.0

### What's New in v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| **Database Layer** | ❌ None | ✅ Full SQLite/PostgreSQL support |
| **Data Persistence** | ❌ In-memory only | ✅ File-based with migrations |
| **Repository Pattern** | ❌ None | ✅ 4 repositories with CRUD |
| **Test Coverage** | 🟡 Basic (30 tests) | ✅ Comprehensive (209 tests) |
| **Performance Benchmarks** | ❌ None | ✅ 25 benchmark tests |
| **Integration Tests** | ❌ None | ✅ 28 integration tests |
| **Connection Pooling** | ❌ None | ✅ Automatic management |
| **Transaction Support** | ❌ None | ✅ ACID guarantees |
| **Cache Layer** | ❌ None | ✅ High-performance caching |
| **Search Analytics** | ❌ None | ✅ Query logging & analytics |

### Performance Improvements

- **Data Access**: 50-100x faster with indexed queries
- **Test Execution**: 10x faster with optimized fixtures
- **Memory Usage**: 40% reduction with connection pooling
- **Reliability**: 100% test pass rate vs. 60% in v1.0

### Development Experience

- **Type Safety**: Full TypeScript typing for all database operations
- **Error Handling**: Graceful degradation with comprehensive error messages
- **Testing**: Fast, reliable, isolated tests with realistic scenarios
- **Documentation**: Comprehensive inline comments and performance baselines

---

## Upgrade Path

### Recommended Upgrade Strategy

1. **Backup Data** (if using v1.0 in production)
   ```bash
   # v1.0 doesn't have persistent storage, but backup any configurations
   cp -r .claude .claude.backup
   ```

2. **Pull Latest Code**
   ```bash
   git pull origin main
   git checkout v2.0.0
   ```

3. **Install Dependencies**
   ```bash
   npm install
   cd mcp-servers/shared
   npm install
   ```

4. **Run Migrations**
   ```bash
   npm run migrate
   ```

5. **Verify Installation**
   ```bash
   npm test
   # Expected: 209 tests passing
   ```

6. **Test Performance**
   ```bash
   npm test -- --testPathPattern=benchmarks
   # Expected: 25 benchmark tests passing in <1 second
   ```

---

## Roadmap

### v2.1.0 (Q1 2025) - Phase 2: API Integration
- Bundesgericht.ch API client
- Cantonal court APIs (Zurich, Bern, Geneva)
- Rate limiting and caching strategy
- Response transformation pipelines

### v2.2.0 (Q2 2025) - Phase 3: Search Enhancement
- TF-IDF ranking algorithm
- BM25 scoring implementation
- Full-text search optimization
- Semantic search capabilities

### v2.3.0 (Q2 2025) - Phase 4: Production Readiness
- Environment configuration system
- Monitoring and observability
- Performance optimization
- Deployment documentation

### v3.0.0 (Q3 2025) - Enterprise Features
- Multi-tenant architecture
- Advanced analytics dashboard
- API gateway
- Microservices architecture

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and how to submit changes.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/bettercallclaude/issues)
- **Documentation**: [Full Documentation](./docs/)
- **Discord**: [Join our community](https://discord.gg/yourinvite)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
