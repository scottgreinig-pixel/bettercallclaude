---
description: "Run three-agent adversarial analysis -- advocate builds the case, adversary challenges it, judicial analyst synthesizes"
---

You are invoked via `/bettercallclaude:adversarial`. Apply the adversarial-analysis skill methodology in full to the user's request.

Supported flags: `--short`, `--medium` (default), `--long`, `--no-summary`. You can also say: "analisi breve" or "analisi approfondita" instead of using flags.

**Output convention**: Write the adversarial review to `bcc-output/YYYY-MM-DD-<slug>/04-adversarial-review.md` and give in chat only a 3–5 line summary with the file path. See `skills/shared/SKILL.md`.

**Plugin scope**: use exclusively BetterCallClaude agents, skills, and MCP servers for all legal work. Do not delegate to external skills or agents. File generation (.docx, .pdf) and system operations are exempt.

$ARGUMENTS
