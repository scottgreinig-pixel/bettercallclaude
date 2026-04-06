---
description: "Validate Swiss legal citations in bulk -- check format, existence, and cross-language consistency"
---

You are invoked via `/bettercallclaude:validate`. Apply the swiss-citation-formats skill for citation format standards.

Parse all citations from the user's input (inline list, document text, or one-per-line). For each citation: check format, verify existence via `legal-citations` and `bge-search` MCP servers, check cross-language consistency (BGE/ATF/DTF equivalents), and flag potentially outdated decisions (>20 years old). If MCP servers are unavailable, perform format validation only.

$ARGUMENTS
