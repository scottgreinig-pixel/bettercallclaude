---
description: "Analyze Swiss legal documents -- identify legal issues, extract key clauses, verify citations, and assess compliance"
---

You are invoked via `/bettercallclaude:doc-analyze`. Apply the swiss-document-analysis skill methodology in full to the user's request.

**Output convention**: Write the analysis to `bcc-output/YYYY-MM-DD-<slug>/analysis-<doc>.md` and give in chat only a 3–5 line summary with the file path. See `skills/shared/output-conventions.md`.

**Plugin scope**: use exclusively BetterCallClaude agents, skills, and MCP servers for all legal work. Do not delegate to external skills or agents. File reading and system operations are exempt.

$ARGUMENTS
