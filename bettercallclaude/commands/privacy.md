---
description: "View or change the BetterCallClaude privacy mode (strict/balanced/cloud)"
---

# BetterCallClaude Privacy Configuration

When this command is invoked, manage the privacy mode setting for the Anwaltsgeheimnis detection hook.

## Behavior

### No arguments or `status`

Display the current privacy mode by reading `~/.betterask/config.yaml`. If the file does not exist or has no `privacy_mode` key, the default is `balanced`.

Output the following formatted block (replace the mode with the actual current value):

```
======================================================
  BetterCallClaude — Privacy Mode
======================================================

  Current mode:  balanced

  Available modes:
  ┌─────────────┬──────────────────────────────────────────────────┐
  │ strict      │ Same pattern matching as balanced but blocks     │
  │             │ (deny) instead of prompting. Ollama exempt.      │
  │             │ MCP servers remain usable for non-privileged.    │
  ├─────────────┼──────────────────────────────────────────────────┤
  │ balanced    │ Strong privilege markers prompt for confirmation │
  │  (default)  │ (ask). Weak markers with legal context also     │
  │             │ prompt. Non-privileged content passes normally.   │
  ├─────────────┼──────────────────────────────────────────────────┤
  │ cloud       │ Strong privilege markers prompt (ask).           │
  │             │ Weak markers allowed without prompt.             │
  │             │ Maximum capability, reduced privacy.             │
  └─────────────┴──────────────────────────────────────────────────┘

  Config file:   ~/.betterask/config.yaml
  Hook:          PreToolUse (Write/Edit/MultiEdit/Bash/WebFetch/MCP)

  To change:     /bettercallclaude:privacy strict
                 /bettercallclaude:privacy balanced
                 /bettercallclaude:privacy cloud

======================================================
```

### Argument is `strict`, `balanced`, or `cloud`

1. Read the existing `~/.betterask/config.yaml` file. If it does not exist, create it.
2. Set or update the `privacy_mode` key to the requested value.
3. Preserve any other keys already in the file.
4. Write the file back.
5. Confirm the change to the user:

```
Privacy mode changed: balanced → strict

The hook will now block all non-Ollama tool calls.
Changes take effect on the next tool call.
```

### Invalid argument

If the argument is not `strict`, `balanced`, `cloud`, or `status` (or empty), respond:

```
Unknown privacy mode: "<argument>"
Valid modes: strict | balanced | cloud

Run /bettercallclaude:privacy to see current status.
```

## Implementation Notes

- The config file path is `~/.betterask/config.yaml`.
- Use Bash to read/write the file. Example read:
  ```bash
  cat ~/.betterask/config.yaml 2>/dev/null || echo "privacy_mode: balanced"
  ```
- Example write (preserving other keys):
  ```bash
  mkdir -p ~/.betterask
  if [ -f ~/.betterask/config.yaml ]; then
    grep -v '^privacy_mode:' ~/.betterask/config.yaml > ~/.betterask/config.yaml.tmp
    mv ~/.betterask/config.yaml.tmp ~/.betterask/config.yaml
  fi
  echo "privacy_mode: strict" >> ~/.betterask/config.yaml
  ```
- The `privacy-check.js` hook reads this file as a fallback when `CLAUDE_PLUGIN_USER_CONFIG` does not contain a `privacy_mode` value.

## User Query

$ARGUMENTS
