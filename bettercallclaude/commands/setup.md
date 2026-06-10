---
description: "Alias for /bettercallclaude:start — will be removed in v5.0. Use /bettercallclaude:start or /bettercallclaude:doctor instead."
---

# BetterCallClaude Setup (Deprecated Alias)

> **Note**: `/bettercallclaude:setup` is now `/bettercallclaude:start`. This alias will be removed in v5.0.
> For diagnostics only, use `/bettercallclaude:doctor`.

When this command is invoked, display a deprecation notice **in the user's language** (detect from their message or default to DE), then execute the full `/bettercallclaude:start` workflow.

Deprecation notice template (adapt to DE/FR/IT/EN):

```
⚠ /bettercallclaude:setup ist jetzt /bettercallclaude:start
  Dieser Alias wird in v5.0 entfernt.
  Nur für Server-Diagnostik: /bettercallclaude:doctor
```

Then proceed with the full `/bettercallclaude:start` command — greeting, MCP check, playbook verification, and examples.

## User Query

$ARGUMENTS
