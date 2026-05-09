---
name: legal-briefing
description: "Proactively suggests or activates a structured briefing session before executing complex Swiss legal queries. Trigger whenever a query: spans multiple legal domains (corporate + tax, employment + social insurance, regulatory + M&A), is multi-jurisdictional (federal + cantonal, Swiss + German/EU), involves both analysis and a deliverable document, mentions financial exposure above CHF 100,000, uses open-ended or uncertain language ('handle', 'deal with', 'advise on', 'figure out', 'not sure how to', 'where do we even start', 'what are my options'), or requires coordinating three or more specialist agents. Activate for: group restructuring, IPO preparation, cross-border M&A, family office setup, FINMA/crypto/AML compliance, shareholder disputes with board deadlock, employment termination with discrimination claims, tenancy disputes spanning cantonal and federal law, startup entity conversions, and any situation where the user cannot identify a single focused legal question. Do NOT trigger for: single-article lookups, citation checks, translation-only requests, single-canton procedural questions, or clearly scoped single-domain questions even if complex."
---

# Legal Briefing Skill

Before routing a complex Swiss legal query to specialist agents, suggest or activate a briefing session. Structured intake prevents mis-routing, avoids wasted effort on the wrong track, and ensures every agent gets exactly the context it needs.

## When to Suggest a Briefing

Suggest proactively — without waiting to be asked — whenever the query meets **any** of these conditions:

### Complexity (suggest when score ≥ 5)
- Three or more legal domains in a single query (e.g., corporate + tax + compliance + FINMA)
- Multi-jurisdictional question (federal + cantonal, or multiple cantons)
- Document output expected alongside analysis (e.g., "analyze and draft")
- Financial exposure above CHF 100,000
- Multiple parties with potentially conflicting interests

### Ambiguity (suggest whenever present)
- Desired output is unclear — is this research, strategy, a document, or a compliance check?
- Jurisdiction cannot be determined from the query
- Open-ended verbs dominate: "handle", "deal with", "figure out", "advise on", "sort out"
- Multiple valid routing paths exist with significantly different outcomes

### Pipeline complexity (suggest when coordination needed)
- Query maps to a known workflow template (litigation-prep, due-diligence, contract-lifecycle)
- Three or more agents would need to coordinate
- Agent outputs depend on each other (output of one feeds into another)

## When NOT to Suggest

Skip the briefing and route directly when:
- Simple, focused question (complexity 1–3) with a clear single answer
- User specifies a single agent explicitly (`@agent_name`)
- User uses `--skip-briefing` or `--direct` flag
- Query is a citation lookup, translation request, or citation format check
- User is resuming a previously approved execution plan

## How to Suggest

When conditions are met, offer the briefing naturally — not as a gate, but as the smart path:

```
💡 This query involves [N domains / multi-jurisdiction / pipeline coordination].
A short briefing session will help me ask the right questions first and build
a precise execution plan — rather than starting on potentially the wrong track.

**Options:**
- **Start briefing** (recommended) — I'll gather key facts, then build a step-by-step plan
- **Skip briefing** — Route directly to agents now (or add `--skip-briefing` to always bypass)
```

If the user chooses to proceed with the briefing, invoke `/bettercallclaude:briefing` with the original query as the argument. If the user skips, route directly via `/bettercallclaude:legal`.

## Integration Points

- **`/legal` gateway**: Check activation criteria here, between intent classification and agent routing.
- **`/bettercallclaude:briefing` command**: The command that runs the full briefing workflow — invoke it when the user agrees to proceed.
- **Orchestrator agent**: Receives the approved execution plan YAML from the briefing session and executes it with checkpoints.

## Quality Standards

- Be helpful, not obstructive — never block a clearly simple query with a briefing suggestion.
- A missed briefing on a complex case causes real harm (wrong agents, wasted effort). When in doubt, suggest.
- The user must always have a clear, friction-free path to skip and proceed directly.
