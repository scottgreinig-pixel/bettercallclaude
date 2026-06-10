# BetterCallClaude — Cowork Compatibility Audit

**Version**: v4.8.1
**Date**: 2026-06-10
**Purpose**: Systematic review of all commands and skills for Cowork-first experience.

---

## Audit Legend

- **Terminal assumptions**: references to `.claude/` only, bash/git instructions, CLI jargon, developer-only examples
- **Output**: chat = output in conversation; file = writes deliverable to working folder
- **Overlap**: functional overlap with another command (see D7 policy)
- **Action**: NONE (already compatible), FIX (modified in this release), NOTE (documented limitation)

---

## Commands Audit Matrix

| # | Command | Terminal Assumptions? | Output | Overlap | Cowork as-is? | Action |
|---|---------|----------------------|--------|---------|----------------|--------|
| 1 | `legal` | No | Chat (routes to agents) | — | Yes | FIX: added natural-language flag descriptions, output convention |
| 2 | `research` | No | Chat (long) | — | Partial | FIX: added output convention (file for memos) |
| 3 | `strategy` | No | Chat (long) | — | Partial | FIX: added output convention |
| 4 | `draft` | No | Chat (long) | — | Partial | FIX: added output convention |
| 5 | `adversarial` | No | Chat (long) | — | Partial | FIX: added output convention |
| 6 | `briefing` | No | Chat (interactive) | — | Yes | FIX: added natural-language flag descriptions |
| 7 | `workflow` | No | Chat (long) | — | Partial | FIX: added output convention |
| 8 | `translate` | No | Chat (long) | — | Partial | FIX: added output convention |
| 9 | `cite` | No | Chat (short) | — | Yes | NONE |
| 10 | `validate` | No | Chat (medium) | — | Yes | NONE |
| 11 | `doc-analyze` | No | Chat (long) | — | Partial | FIX: added output convention |
| 12 | `nda-triage` | No | Chat (long) | — | Partial | FIX: added output convention |
| 13 | `precedent` | No | Chat (long) | — | Partial | FIX: added output convention |
| 14 | `summarize` | No | Chat (short-medium) | — | Yes | NONE |
| 15 | `refine` | No | Chat (interactive) | — | Yes | NONE |
| 16 | `legal-5step` | No | Chat (very long) | — | Partial | FIX: added output convention |
| 17 | `federal` | No | Chat (medium) | — | Yes | NONE |
| 18 | `cantonal` | No | Chat (medium) | — | Yes | NONE |
| 19 | `setup` | Yes: `curl`, `bash`, `claude plugin list`, `node --version` | Chat | **Overlap with `start`** | Partial | FIX: converted to alias of `start` with deprecation notice (D7) |
| 20 | `privacy` | Yes: `bash`, `cat`, `grep`, `mkdir -p`, `~/.betterask/` paths | Chat | — | Partial | FIX: replaced bash instructions with natural-language guidance |
| 21 | `version` | Minor: "Run `/bettercallclaude:setup` to check connectivity" | Chat | — | Yes | FIX: updated reference to `/bettercallclaude:doctor` |
| 22 | `help` | No | Chat | — | Yes | FIX: added `start`, `doctor`; updated `setup` entry as alias |

---

## Skills Audit Matrix

| # | Skill | Terminal Assumptions? | Uses MCP? | Reduced Mode Declared? | Action |
|---|-------|----------------------|-----------|------------------------|--------|
| 1 | `swiss-legal-research` | No | Yes (7 servers) | **Yes** | NONE |
| 2 | `swiss-legal-drafting` | `.claude/` in playbook path (ok, also searches shared folder) | Yes (fedlex, citations) | No | FIX: added reduced mode section |
| 3 | `swiss-legal-strategy` | `.claude/` in playbook path (ok) | Yes (entscheidsuche, swiss-caselaw) | No | FIX: added reduced mode section |
| 4 | `swiss-document-analysis` | `.claude/` in playbook path (ok) | Yes (6 servers) | No | FIX: added reduced mode section |
| 5 | `swiss-citation-formats` | No | Yes (legal-citations, swiss-caselaw, fedlex) | No | FIX: added reduced mode section |
| 6 | `swiss-jurisdictions` | No | Yes (entscheidsuche) | No | FIX: added reduced mode section |
| 7 | `swiss-legal-translation` | No | Yes (legal-citations, fedlex) | No | FIX: added reduced mode section |
| 8 | `adversarial-analysis` | No | Yes (swiss-caselaw, entscheidsuche, bge-search) | No | FIX: added reduced mode section |
| 9 | `compliance-frameworks` | No | Yes (fedlex, entscheidsuche, onlinekommentar) | No | FIX: added reduced mode section |
| 10 | `data-protection-law` | No | Yes (entscheidsuche, swiss-caselaw, fedlex, onlinekommentar) | No | FIX: added reduced mode section |
| 11 | `privacy-routing` | Refs to `PreToolUse` hook, `userConfig` | Local (ollama) | Partial (privacy routing table) | FIX: added Cowork fallback section (D5) |
| 12 | `legal-briefing` | No | No (orchestration only) | N/A | NONE |
| 13 | `output-summarization` | No | No | N/A | NONE |
| 14 | `legal-query-refinement` | Minor MCP ref | Minimal | N/A | NONE |
| 15 | `legal-5step-framework` | No | Yes (via sub-commands) | Inherits from sub-skills | NONE |

---

## Overlap Resolution Register (D7)

| Old Command | New Command | Reason | All Features Preserved? | Alias Active? |
|-------------|-------------|--------|------------------------|---------------|
| `setup` | `start` | `start` provides onboarding + connectivity check; `setup` was connectivity-only | Yes — `start` includes full MCP diagnostics (reuses `doctor` logic) plus onboarding, playbook setup, and examples | Yes — `setup` executes `start` and shows deprecation notice until v5.0 |

No other overlaps identified in this audit.

---

## Hooks Verification (D5)

### PreToolUse Hook (privacy-routing / Anwaltsgeheimnis)

**Status**: The `PreToolUse` hook is a Claude Code / Cowork platform feature. Both environments support `hooks` in the plugin configuration. The hook intercepts `Write`, `Edit`, `MultiEdit`, `Bash`, `WebFetch`, and all MCP tool calls (`mcp__.*`).

**Cowork behavior**: Cowork Desktop executes hooks as defined in the plugin's `CLAUDE.md` or `settings.json`. The PreToolUse hook for privacy-routing is expected to function identically in both environments because it runs as a JavaScript module evaluated by the Claude runtime, not as an external process.

**Fallback**: As a defense-in-depth measure, the `privacy-routing` SKILL.md now includes a skill-level fallback section that instructs Claude to apply the same privacy checks even if the hook mechanism is unavailable. This ensures Art. 321 StGB protection does not depend solely on the hook.

### Workflow Enforcement Hook (legal-5step)

**Status**: The 5-step framework enforcement operates at the skill/command level (sequential agent invocation), not via a platform hook. It functions identically in both environments.

---

## Candidates for Future Consolidation (Spec D)

These are noted for reference only — no action taken in this release:

| Candidate | Observation |
|-----------|-------------|
| `research` + `precedent` | Significant overlap in BGE search; `precedent` focuses on chain tracking |
| `cite` + `validate` | Both work with citations; `validate` is batch mode of `cite` |
| `legal` + `legal-5step` | `legal-5step` is a structured superset of multi-agent `legal` workflows |

---

*This audit serves as the regression register for future releases. Update this matrix when adding or modifying commands/skills.*
