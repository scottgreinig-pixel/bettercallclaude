[![Version](https://img.shields.io/badge/version-4.1.2-blue)](https://github.com/fedec65/bettercallclaude/releases)
[![License: AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Cowork%20%7C%20Claude%20Code-orange)](https://claude.ai)
[![Website](https://img.shields.io/badge/web-bettercallclaude.ch-brightgreen)](https://bettercallclaude.ch)
[![MCP Servers](https://img.shields.io/badge/MCP%20servers-6-purple)](https://mcp.bettercallclaude.ch/health)
[![Buy Me a Coffee](https://img.shields.io/badge/support-Buy%20Me%20a%20Coffee-yellow)](https://buymeacoffee.com/federicocesconi)

# BetterCallClaude

**Swiss Legal Intelligence Plugin for Cowork and Claude Code**

BetterCallClaude transforms legal research, case strategy, and document drafting for Swiss lawyers. It provides deep integration with Swiss legal databases, multi-lingual analysis (DE/FR/IT/EN), and built-in Anwaltsgeheimnis (attorney-client privilege) protection -- 21 agents, 19 commands, 10 skills, and 6 MCP servers covering BGE/ATF/DTF precedent research, litigation strategy, adversarial analysis, legal drafting, and citation verification across all 26 Swiss cantons.

## Overview

### The Framework at a Glance

BetterCallClaude provides a structured methodology for handling legal work with AI assistance. The framework consists of five interconnected phases.

![BetterCallClaude Framework](docs/images/bettercallclaude_framework.png)

---

## What's New in v4.1.2

**Windows 11 fix: cross-platform privacy hook** -- The Anwaltsgeheimnis PreToolUse hook has been rewritten in Node.js (replaces bash script). This fixes `/setup` freezing and commands not loading on Windows 11 Cowork Desktop where `bash` is not natively available.

- **Cross-platform**: hook now runs on Windows, macOS, and Linux without any shell dependency
- **Same protection**: identical pattern matching (14 Anwaltsgeheimnis patterns, DE/FR/IT + legal refs)
- **No setup required**: Node.js is always available in Cowork environments

## What's New in v4.1.1

**Legal Prompt Engineer Agent + /refine command** -- New specialist transforms vague queries into structured legal prompts through Socratic dialogue, with workflow recommendations and multi-lingual terminology guidance.

- **Two invocation paths**: `/bettercallclaude:refine [query]` or `/bettercallclaude:legal --refine [query]`
- **Socratic refinement**: Interactive dialogue fills gaps (jurisdiction, domain, party position)
- **Workflow recommendations**: Suggests optimal agent pipelines (e.g., researcher → strategist → drafter)
- **Mode flags**: `--quick` for fast results, `--optimize` for experienced users

[Full changelog →](https://github.com/fedec65/bettercallclaude/blob/main/bettercallclaude/changelog.md)

---

## Quick Install

### Cowork Desktop (Recommended)

1. In Cowork, click **Customize** > **Browse plugins** > **Personal** > **+** > **Add marketplace from GitHub**
2. Enter `fedec65/bettercallclaude` and click **Sync**
3. Click **Install** on the BetterCallClaude card

### Claude Code CLI

```
claude plugin marketplace add fedec65/bettercallclaude
claude plugin install bettercallclaude@bettercallclaude-marketplace
```

### Windows

Install [Git for Windows](https://git-scm.com/downloads/win), then install Claude Code (`winget install Anthropic.ClaudeCode`), then run the CLI commands above.

### Team Setup

Add to your project's `.claude/settings.json` so anyone who clones the repo gets prompted to install:

```json
{
  "extraKnownMarketplaces": {
    "bettercallclaude-marketplace": {
      "source": { "source": "github", "repo": "fedec65/bettercallclaude" }
    }
  }
}
```

**Full installation guide, visual setup, and tutorials:** [BetterCallClaude Tutorial](https://github.com/fedec65/bettercallclaude_tutorial)

---

## Commands

| Command | Description |
|---------|-------------|
| `/bettercallclaude:legal` | Intelligent gateway -- analyzes intent, routes to the appropriate specialist agent, and manages multi-step legal workflows. Use `--refine` to transform vague queries first. |
| `/bettercallclaude:refine` | Transform vague legal queries into structured prompts through Socratic dialogue. Recommends optimal workflows and introduces Swiss legal terminology. Flags: `--quick` (skip dialogue), `--optimize` (for experienced users). |
| `/bettercallclaude:research` | Search Swiss legal precedents and compile research memoranda. Supports BGE/ATF/DTF databases, doctrine references, and cross-jurisdictional analysis. |
| `/bettercallclaude:strategy` | Develop litigation strategy with risk assessment, cost-benefit analysis, and procedural pathway evaluation. |
| `/bettercallclaude:draft` | Draft Swiss legal documents including contracts, court briefs, legal opinions, and memoranda with proper citation formatting. |
| `/bettercallclaude:cite` | Verify and format Swiss legal citations across all four national languages (BGE/ATF/DTF formats). |
| `/bettercallclaude:validate` | Validate Swiss legal citations in bulk -- check format, existence, and cross-language consistency. |
| `/bettercallclaude:precedent` | Search and analyze BGE/ATF/DTF precedents with precedent chain tracking and evolution analysis. |
| `/bettercallclaude:federal` | Analyze a legal question under federal Swiss law (ZGB, OR, StGB, BV, and related federal statutes). |
| `/bettercallclaude:cantonal` | Analyze a legal question under cantonal law for a specific canton. |
| `/bettercallclaude:adversarial` | Run three-agent adversarial analysis -- advocate builds the case, adversary challenges it, judicial analyst synthesizes. |
| `/bettercallclaude:briefing` | Structured pre-execution briefing session -- assembles a specialist panel, collects case context, and builds an execution plan before agents start working. |
| `/bettercallclaude:workflow` | Define and execute multi-agent legal workflows (due diligence, litigation prep, contract lifecycle, real estate closing). |
| `/bettercallclaude:translate` | Translate Swiss legal documents between DE, FR, IT, and EN while preserving legal terminology precision. |
| `/bettercallclaude:doc-analyze` | Analyze Swiss legal documents -- identify legal issues, extract key clauses, verify citations, assess compliance. |
| `/bettercallclaude:summarize` | Consolidate multi-agent pipeline output -- deduplicate disclaimers, terminology, and citations with length control (`--short`/`--medium`/`--long`). |
| `/bettercallclaude:setup` | Check MCP server connectivity and switch between HTTP/local transport. |
| `/bettercallclaude:version` | Display plugin version, installed components, and system status. |
| `/bettercallclaude:help` | Show complete command reference, available agents, skills, and usage examples. |

### Usage Examples

```
/bettercallclaude:legal I need to assess our exposure under Art. 97 OR for late delivery

/bettercallclaude:refine I have problems with my landlord

/bettercallclaude:refine --quick My employer fired me without notice

/bettercallclaude:research Art. 97 OR contractual liability for late delivery

/bettercallclaude:strategy Commercial lease dispute in Zurich, landlord claims CHF 200k damages

/bettercallclaude:draft Employment contract for a software engineer in Geneva, bilingual DE/FR

/bettercallclaude:adversarial Is the non-compete clause in this employment contract enforceable?

/bettercallclaude:workflow litigation-prep Personal injury claim against manufacturer

/bettercallclaude:briefing Prepare full litigation for Art. 97 OR breach, CHF 500K, Zurich

/bettercallclaude:cantonal ZH Commercial court jurisdiction for contract disputes over CHF 30k

/bettercallclaude:doc-analyze @contract.pdf Review this commercial lease agreement
```

---

## Key Features

- **Briefing sessions** -- Complex queries trigger a collaborative intake phase with specialist panels, targeted questions, and structured execution plans before agents start working. Supports `--resume` for cross-session persistence.
- **Adversarial analysis** -- Three-agent workflow: advocate builds the case, adversary challenges it, judicial analyst synthesizes using Swiss Erwagung methodology with probability scores.
- **Multi-agent workflows** -- Predefined pipelines for due diligence, litigation prep, contract lifecycle, and real estate closings.
- **All 26 cantons** -- Full cantonal coverage with court systems, citation formats, and MCP search via entscheidsuche.ch. Federal law is the default; mentioning a canton triggers cantonal mode.
- **Multi-language** -- Automatic language detection for DE/FR/IT/EN with correct legal terminology and citation formats.

---

## MCP Servers & Transport

| Server | Purpose | Transport |
|--------|---------|-----------|
| `entscheidsuche` | Swiss court decision search (Bundesgericht + cantonal) | HTTP |
| `bge-search` | Federal Supreme Court decision search | HTTP |
| `legal-citations` | Citation verification and formatting | HTTP |
| `fedlex-sparql` | Federal legislation database (SPARQL) | HTTP |
| `onlinekommentar` | Swiss legal commentaries | HTTP |
| `ollama` | Local privacy classification | Local (stdio) |

The five HTTP servers connect to `https://mcp.bettercallclaude.ch` (rate limit: 60 req/min per IP). No API keys required. The ollama server runs locally for Anwaltsgeheimnis detection.

To switch to local stdio transport: `/bettercallclaude:setup --local` (requires Node.js 18+). Switch back: `/bettercallclaude:setup --restore-http`.

See [CONNECTORS.md](bettercallclaude/CONNECTORS.md) for detailed API documentation.

---

## Privacy

BetterCallClaude includes built-in Anwaltsgeheimnis (attorney-client privilege, Art. 321 StGB) compliance. A `PreToolUse` hook scans outgoing tool calls for privilege indicators in German (Anwaltsgeheimnis, Mandantengeheimnis, vertraulich), French (secret professionnel, confidentiel), and Italian (segreto professionale, confidenziale).

| Mode | Behavior |
|------|----------|
| `strict` | All external calls require confirmation. Local processing preferred via Ollama. |
| `balanced` | Privileged content triggers confirmation. Non-privileged content processed normally. |
| `cloud` | Standard cloud processing with privacy hook active for explicit privilege markers only. |

---

## Language Support

| Language | Code | Legal Context |
|----------|------|---------------|
| German | DE | Primary: ZGB, OR, StGB, BGE. Used in ZH, BE, BS, and German-speaking cantons. |
| French | FR | Official: CC, CO, CP, ATF. Used in GE, VD, and French-speaking cantons. |
| Italian | IT | Official: CC, CO, CP, DTF. Used in TI and Italian-speaking regions. |
| English | EN | Working language with Swiss legal term mapping. |

---

## Requirements

- Cowork or Claude Code (latest version)
- Node.js >= 18 (only for `--local` mode or the ollama privacy classifier)

---

## Author

Federico Cesconi -- [fedec65/bettercallclaude](https://github.com/fedec65/bettercallclaude) -- [bettercallclaude.ch](https://bettercallclaude.ch)

## License

AGPL-3.0 -- See [LICENSE](LICENSE) for full terms.

[Support the project](https://buymeacoffee.com/federicocesconi)

---

## For Developers

The `mcp-servers-src/` directory contains TypeScript source for all six MCP servers. The `mcp-servers-http/` directory contains the HTTP transport wrapper deployed to Railway.

```bash
npm run build          # Compile TypeScript
npm run build:bundle   # Build single-file bundles into mcp-servers/*/dist/
npm test               # Run tests
npm run package        # Create distributable plugin zip
```

Compiled bundles in `bettercallclaude/mcp-servers/*/dist/` are checked into git so end users don't need build tooling. See [CONNECTORS.md](bettercallclaude/CONNECTORS.md) for MCP server API documentation.

---

## Professional Disclaimer

BetterCallClaude is a legal research and analysis tool. All outputs produced by this plugin:

- Require professional lawyer review and validation before use.
- Do not constitute legal advice.
- May contain errors, omissions, or outdated information.
- Must be verified against official sources (admin.ch, court databases, official gazettes).
- Must be adapted to the specific circumstances of each case.

Lawyers maintain full professional responsibility for all legal work products. This tool assists legal professionals but does not replace professional judgment, independent verification, or the duty of care owed to clients.
