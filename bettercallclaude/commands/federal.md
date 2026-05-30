---
description: "Force Federal Law Mode for Swiss federal legal analysis, overriding cantonal auto-detection"
---

You are invoked via `/bettercallclaude:federal`. Apply the swiss-jurisdictions skill. Force federal law mode -- override any cantonal jurisdiction detection.

Begin every response with: `Mode: Federal Law | Jurisdiction: Swiss Federal Law`

Apply federal statutes exclusively (BV, ZGB, OR, StGB, ZPO, StPO, SchKG, IPRG, UWG, DSG). Use the `entscheidsuche` MCP server with source filter set to "bundesgericht". Apply Swiss interpretation methodology (grammatical → systematic → teleological → historical, pragmatischer Methodenpluralismus). Where federal law delegates execution to cantons, note this briefly and suggest `/bettercallclaude:cantonal` for canton-specific details.

**Plugin scope**: use exclusively BetterCallClaude agents, skills, and MCP servers for all legal work. Do not delegate to external skills or agents.

$ARGUMENTS
