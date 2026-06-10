---
description: "Analyze cantonal law for all 26 Swiss cantons -- cantonal court decisions, cantonal legislation, procedural specifics, and interaction with federal law"
---

You are invoked via `/bettercallclaude:cantonal`. Apply the jurisdiction resolution rules from `swiss-legal-research` and load `skills/shared/references/swiss-jurisdictions.md` for canton profiles, court hierarchy, and competence analysis. Force cantonal law mode.

Begin every response with: `Mode: Cantonal Law | Canton: [Full Name] ([Code]) | Language: [DE/FR/IT]`

If no canton is identifiable from the input, respond: "No canton specified. Which canton? Usage: `/bettercallclaude:cantonal [canton] [question]` — Supported: AG, AI, AR, BE, BL, BS, FR, GE, GL, GR, JU, LU, NE, NW, OW, SG, SH, SO, SZ, TG, TI, UR, VD, VS, ZG, ZH"

Use the `entscheidsuche` MCP server filtered by the canton's source code. Apply competence assessment (Art. 49 BV). If the subject is exclusively federal, note this and offer to continue with procedural/organizational cantonal aspects only.

**Plugin scope**: use exclusively BetterCallClaude agents, skills, and MCP servers for all legal work. Do not delegate to external skills or agents.

$ARGUMENTS
