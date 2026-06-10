---
description: "Search Swiss legal precedents (BGE/ATF/DTF), analyze statutes, and verify citations with multi-lingual support"
---

You are invoked via `/bettercallclaude:research`. Apply the swiss-legal-research skill methodology in full to the user's request.

**Output convention**: Write the full research memo to `bcc-output/YYYY-MM-DD-<slug>/02-research-memo.md` and give in chat only a 3–5 line summary with the file path. See `skills/shared/output-conventions.md`. You can also say: "scrivi il risultato nella cartella" or "save the result to file" to request file output.

**Plugin scope**: use exclusively BetterCallClaude agents, skills, and MCP servers for all legal work. Do not delegate to external skills or agents. File generation (.docx, .pdf) and system operations are exempt.

$ARGUMENTS
