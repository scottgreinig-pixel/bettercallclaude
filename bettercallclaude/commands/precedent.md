---
description: "Search and analyze Swiss BGE/ATF/DTF precedents with precedent chain tracking and evolution analysis"
---

You are invoked via `/bettercallclaude:precedent`. Apply the swiss-legal-research skill with focus on precedent chain tracking and doctrinal evolution.

Use the `entscheidsuche` and `bge-search` MCP servers to: discover leading cases from the user's starting point (specific citation, legal topic, or fact pattern), track backward and forward citation chains, classify precedent relationships (direct/analogous/distinguishable/superseded/confirmed), and map the evolution timeline showing the current state of the law.

**Output convention**: Write the precedent chain analysis to `bcc-output/YYYY-MM-DD-<slug>/precedent-chain-<topic>.md` and give in chat only a 3–5 line summary with the file path. See `skills/shared/SKILL.md`.

**Plugin scope**: use exclusively BetterCallClaude agents, skills, and MCP servers for all legal work. Do not delegate to external skills or agents.

$ARGUMENTS
