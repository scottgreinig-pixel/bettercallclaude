---
description: "Validate, format, and look up Swiss legal citations including BGE/ATF/DTF decisions and statutory references"
---

You are invoked via `/bettercallclaude:cite`. Apply the swiss-citation-formats skill for citation format standards.

Determine from the user's input which task to perform: validate, look up, convert between languages (BGE/ATF/DTF), generate bibliography, or correct a malformed citation. Use the `legal-citations` and `entscheidsuche` MCP servers. If MCP servers are unavailable, perform format validation only and mark citations as format-checked only.

$ARGUMENTS