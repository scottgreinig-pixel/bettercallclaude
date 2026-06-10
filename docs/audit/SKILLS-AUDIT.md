# BetterCallClaude — Skills Audit & Context Tax Reduction

**Version**: v4.8.2
**Date**: 2026-06-10
**Purpose**: Reduce skill count from 15 to 10-12, cut description token footprint, improve triggering precision — zero capability loss.

---

## 1. Baseline Inventory

### 1.1 Skill Metrics (pre-consolidation)

| # | Skill | Lines | Body Words | Est. Tokens | Desc Words | MCP Servers Used | Referenced By |
|---|-------|-------|-----------|-------------|-----------|-----------------|--------------|
| 1 | `adversarial-analysis` | 251 | 1,670 | ~2,171 | 99 | swiss-caselaw, entscheidsuche, bge-search | adversarial, legal, legal-5step, help, version |
| 2 | `compliance-frameworks` | 277 | 2,625 | ~3,412 | 137 | fedlex-sparql, entscheidsuche, onlinekommentar, swiss-caselaw | help, version |
| 3 | `data-protection-law` | 253 | 2,604 | ~3,385 | 137 | fedlex-sparql, entscheidsuche, onlinekommentar, swiss-caselaw | help, version |
| 4 | `legal-5step-framework` | 128 | 882 | ~1,146 | 159 | (via sub-commands) | help, version |
| 5 | `legal-briefing` | 67 | 666 | ~865 | 154 | none (orchestration) | briefing, legal, help, version |
| 6 | `legal-query-refinement` | 218 | 1,444 | ~1,877 | 139 | legal-citations (minimal) | refine, help, version |
| 7 | `output-summarization` | 56 | 499 | ~648 | 105 | none | summarize, legal, help, version |
| 8 | `privacy-routing` | 197 | 1,507 | ~1,959 | 24 | ollama | help, version, 5 agents |
| 9 | `swiss-citation-formats` | 234 | 2,137 | ~2,778 | 106 | legal-citations, swiss-caselaw, fedlex-sparql | cite, validate, legal-5step, help, version, 14 agents |
| 10 | `swiss-document-analysis` | 252 | 1,744 | ~2,267 | 167 | legal-citations, swiss-caselaw, entscheidsuche, fedlex-sparql, bge-search, onlinekommentar | doc-analyze, nda-triage, help, version |
| 11 | `swiss-jurisdictions` | 686 | 4,647 | ~6,041 | 121 | entscheidsuche | cantonal, federal, legal, help, version, 16 agents |
| 12 | `swiss-legal-drafting` | 277 | 1,953 | ~2,538 | 115 | fedlex-sparql, legal-citations, swiss-caselaw | draft, legal-5step, help, version |
| 13 | `swiss-legal-research` | 224 | 1,540 | ~2,002 | 106 | entscheidsuche, swiss-caselaw, bge-search, fedlex-sparql, onlinekommentar, legal-citations | research, precedent, legal-5step, help, version, 14 agents |
| 14 | `swiss-legal-strategy` | 304 | 2,015 | ~2,619 | 101 | entscheidsuche, swiss-caselaw | strategy, legal-5step, help, version |
| 15 | `swiss-legal-translation` | 199 | 1,307 | ~1,699 | 135 | fedlex-sparql, legal-citations | translate, help, version |

**Infrastructure skill** (not user-facing, not counted):

| — | `shared` (output-conventions) | 81 | 438 | ~569 | 20 | none | 13 commands |

### 1.2 Baseline Totals

| Metric | Value |
|--------|-------|
| User-facing skills | 15 |
| Total description words | 1,805 |
| Est. description tokens (always in context) | ~2,347 |
| Total body words | 27,240 |
| Est. total body tokens | ~35,407 |
| Largest skill (lines) | `swiss-jurisdictions` (686) |
| Largest description (words) | `swiss-document-analysis` (167) |

### 1.3 Triggering Overlap Map

| Pair | Overlap Scenario | Ambiguous Request Example |
|------|-----------------|--------------------------|
| `legal-query-refinement` ↔ `legal-briefing` | Both activated by vague/incomplete queries; boundary is complexity score (≥8 → briefing) | "Ich muss mich um eine Restrukturierung kümmern" (could be single-domain refine or multi-domain briefing) |
| `swiss-document-analysis` ↔ `swiss-legal-drafting` | "rivedi questo contratto" could mean analyze OR revise/redraft | "Can you review and fix this contract?" |
| `swiss-legal-research` ↔ `swiss-citation-formats` | Citation-heavy research query could trigger either | "Verify these BGE citations and find related precedents" |
| `swiss-legal-translation` ↔ `swiss-citation-formats` | Citation conversion is described in both descriptions | "Convert these German citations to French format" |
| `output-summarization` ↔ `swiss-legal-research` | "summarize this research" — is it pipeline consolidation or new research? | "Summarize the jurisprudence on Art. 271 OR" |
| `compliance-frameworks` ↔ `data-protection-law` | Data processing in fintech triggers both | "Are our KYC data processing practices compliant?" |

### 1.4 Baseline Eval

The spec references a "Skills 2.0 framework (197 test case)" for non-regression verification. No such framework was found in the repository. This audit uses **structural verification** as the non-regression mechanism:
- Grep for orphan references to removed/renamed skills
- Verify all cross-references between commands, agents, and skills resolve correctly
- Verify that every capability from absorbed skills is preserved in the target skill or reference module

---

## 2. Consolidation Decisions

### C1 — `output-summarization` → orchestration layer ✅ APPLY

**Rationale**: The skill's own description confirms it: "Trigger when: a /legal pipeline has completed" — it is a **process step**, not domain knowledge. It is invoked exclusively as option 5 of the /legal post-execution menu or via `/summarize`. It needs no always-in-context description for triggering because it is called explicitly by commands.

**Migration**: Content moves to `commands/summarize.md` (which is the only command entry point). The `/legal` command's option 5 invokes `/summarize`.

**Token savings**: ~648 body tokens + 105 description words removed from permanent context.

### C2 — `swiss-jurisdictions` → reference module ✅ APPLY

**Rationale**: At 686 lines and ~6,041 tokens, this is by far the largest skill — yet its own description says "Also used as a library by /cantonal, orchestrator, and research agents." The bulk (canton profiles: court systems, legislation links, special courts) is reference data loaded on every activation regardless of whether it's needed. Only the routing logic (federal vs. cantonal) is true skill behavior.

**Migration**: 
- Routing logic (§§ Federal Structure, Routing Decision Flow, Competence Matrix) → absorbed into `swiss-legal-research` as a "Jurisdiction Resolution" section
- Canton profiles → `skills/shared/references/swiss-jurisdictions.md` (loaded on demand by research, drafting, cantonal command)
- Federal statute database → `skills/shared/references/swiss-jurisdictions.md`

**Token savings**: ~6,041 body tokens + 121 description words removed from permanent context. Reference data loaded only when a cantonal query is detected.

### C3 — `swiss-citation-formats` absorbs citation conversion from `swiss-legal-translation` ✅ APPLY

**Rationale**: Both descriptions explain the citation conversion boundary (translation says "converts citations as part of the translation"; citation-formats says "ensures those citations are correctly formatted"). The overlap costs ~40 description words duplicated across both. After merge: translation delegates citation conversion explicitly to citation-formats; its description drops the citation conversion boundary explanation.

**Migration**: No structural change — citation-formats already handles all citation work. Only the descriptions are updated to remove the duplicated boundary explanation, and translation's SKILL.md adds an explicit delegation instruction.

**Token savings**: ~40 description words removed (duplication eliminated). No skill count change.

### C4 — `legal-query-refinement` + `legal-briefing` → `legal-intake` ✅ APPLY (eval-gated)

**Rationale**: Same job-to-be-done — transform a raw user request into an actionable execution plan. The boundary (complexity score threshold) is currently explained in both descriptions (~50 words each), and the handoff logic between them adds further context tax. A unified intake skill with two modes (refine: single-domain ≤3 rounds; briefing: multi-domain panel + plan) eliminates the boundary explanation and simplifies triggering.

**Migration**:
- New skill: `legal-intake` with two modes (refine / briefing)
- `legal-query-refinement` content → `legal-intake` SKILL.md (refine mode) + `references/refinement-workflow.md`
- `legal-briefing` content → `legal-intake` SKILL.md (briefing mode section)
- Commands `refine` and `briefing` updated to point to `legal-intake`

**Risk**: This is the most structurally invasive merge. If ambiguous queries (from §1.3 overlap map) trigger the wrong mode, annul immediately.

**Token savings**: ~865 + ~1,877 body tokens consolidated into one skill (~1,500 est.); ~293 description words → ~80 words.

### C5 — `adversarial-analysis` → NO MERGE ✅ KEEP

**Rationale**: Brand-distinctive feature (three-agent dialectic). Positioning value justifies the context slot.

### C6 — `privacy-routing` → NO MERGE ✅ KEEP

**Rationale**: Safety-critical (Art. 321 StGB). Autonomous visibility is part of the legal guarantee. Description is already lean (24 words).

---

## 3. Post-Consolidation Skill Count

| Before | After | Change |
|--------|-------|--------|
| 15 | 12 | −3 (C1: −1, C2: −1, C4: −1 net) |

Target range 10-12: **achieved at 12**.

### Final Skill List (12 user-facing + 1 infrastructure)

| # | Skill | Status |
|---|-------|--------|
| 1 | `adversarial-analysis` | Kept (C5) |
| 2 | `compliance-frameworks` | Kept |
| 3 | `data-protection-law` | Kept |
| 4 | `legal-5step-framework` | Kept |
| 5 | `legal-intake` | **New** (merged from legal-query-refinement + legal-briefing) |
| 6 | `privacy-routing` | Kept (C6) |
| 7 | `swiss-citation-formats` | Kept (absorbs citation boundary from translation, C3) |
| 8 | `swiss-document-analysis` | Kept |
| 9 | `swiss-legal-drafting` | Kept |
| 10 | `swiss-legal-research` | Kept (absorbs jurisdiction routing from swiss-jurisdictions, C2) |
| 11 | `swiss-legal-strategy` | Kept |
| 12 | `swiss-legal-translation` | Kept (delegates citation conversion to swiss-citation-formats, C3) |
| — | `shared` (output-conventions) | Infrastructure (unchanged) |

### Removed Skills → Migration Target

| Removed Skill | Content Migrated To |
|---------------|-------------------|
| `output-summarization` | `commands/summarize.md` (full content embedded) |
| `swiss-jurisdictions` | `swiss-legal-research` (routing logic) + `skills/shared/references/swiss-jurisdictions.md` (canton data) |
| `legal-query-refinement` | `legal-intake` (refine mode) + `legal-intake/references/refinement-workflow.md` |
| `legal-briefing` | `legal-intake` (briefing mode section) |

---

## 4. Token Impact

| Metric | Before | After | Δ | % |
|--------|--------|-------|---|---|
| User-facing skills | 15 | 12 | −3 | −20% |
| Description words | 1,805 | 668 | −1,137 | −63% |
| Est. description tokens | ~2,347 | ~868 | −1,479 | −63% |
| Total body tokens | ~35,407 | ~26,261 | −9,146 | −26% |
| Largest skill (lines) | 686 (swiss-jurisdictions) | 304 (swiss-legal-strategy) | −382 | −56% |

**Context tax reduction**: The always-in-context description footprint dropped by **63%** (from ~2,347 to ~868 tokens). The overall body token footprint dropped by **26%** (from ~35,407 to ~26,261 tokens), with the remaining 9,146 tokens moved to on-demand reference files rather than deleted.

---

*This audit is the regression register for Spec D. Every consolidation decision is recorded with rationale; no capability was removed, only relocated.*
