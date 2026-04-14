---
description: "Check MCP server connectivity and switch between HTTP/local transport"
---

# BetterCallClaude MCP Server Setup

When this command is invoked, perform the following diagnostic and transport management workflow.

## Step 1: Check Health Endpoint

Run this command via Bash to check the HTTP MCP service:

```bash
curl -sf https://mcp.bettercallclaude.ch/health
```

If the health check succeeds, the HTTP service is online. If it fails, note the error for the status table.

## Step 2: Probe MCP Servers

Check connectivity for each of the 7 MCP servers using a **two-stage non-blocking approach**:

**Stage A — Check tool availability (non-blocking)**

Look at your currently available tools. For each server, check whether its tools appear in your tool list:

| Server | Tools to look for |
|--------|-------------------|
| bettercallclaude-entscheidsuche | `search_decisions`, `get_decision_details`, etc. |
| bettercallclaude-bge-search | `search_bge`, `get_bge_decision`, etc. |
| bettercallclaude-legal-citations | `validate_citation`, `format_citation`, etc. |
| bettercallclaude-fedlex-sparql | `search_legislation`, `get_article`, etc. |
| bettercallclaude-onlinekommentar | `search_commentaries`, `get_commentary`, etc. |
| swiss-caselaw | `search_decisions`, `find_citations`, `find_appeal_chain`, etc. |
| bettercallclaude-ollama | `ollama_check_status`, `ollama_list_models`, etc. |

**If a server's tools do not appear in your available tool list, mark it as `[ ] Not connected` immediately and move on — do not attempt to call any of its tools.**

**Stage B — Lightweight call (only for servers confirmed available in Stage A)**

For each server whose tools ARE available, make one lightweight call to confirm it responds:

| Server | Lightweight test |
|--------|-----------------|
| bettercallclaude-entscheidsuche | `search_decisions` with a minimal query |
| bettercallclaude-bge-search | `search_bge` with a minimal query |
| bettercallclaude-legal-citations | `validate_citation` with a simple citation |
| bettercallclaude-fedlex-sparql | `search_legislation` with a minimal query |
| bettercallclaude-onlinekommentar | `search_commentaries` with a minimal query |
| swiss-caselaw | `search_decisions` with a minimal query |
| bettercallclaude-ollama | `ollama_check_status` |

If a tool call does not respond promptly, mark that server as `[ ] Timeout` and continue — do not wait or retry.

## Step 3: Display Status Table

For each server, determine the transport type by checking whether the server is configured as HTTP (from `.mcp.json` plugin defaults) or stdio (from a user-scoped override via `claude mcp list`).

Output the following formatted status report, replacing status indicators and transport types based on Steps 1-2:

```
==============================================
  BetterCallClaude MCP Server Status
==============================================

  Server                    Status              Transport
  ------                    ------              ---------
  entscheidsuche            [x] Connected       HTTP
  bge-search                [x] Connected       HTTP
  legal-citations           [x] Connected       HTTP
  fedlex-sparql             [x] Connected       HTTP
  onlinekommentar           [x] Connected       HTTP
  swiss-caselaw             [x] Connected       SSE
  ollama                    [x] Connected       Local

  HTTP Service: https://mcp.bettercallclaude.ch
  Health: OK / Unreachable
  Connected: X/7 servers
==============================================
```

Mark each server as `[x] Connected`, `[ ] Not connected`, or `[ ] Timeout` based on Step 2 results. Show `HTTP` or `Local` in the Transport column.

## Step 4: Provide Guidance Based on Results

### If all 7 servers are connected:

```
All 7 MCP servers are operational. No action needed.
BetterCallClaude is running at full capability.
```

### If HTTP servers are not connected but health check passed:

The HTTP service is online but the servers are not registering. Suggest:

```
The HTTP service is healthy but servers are not connecting.
Try restarting Claude Code or Cowork to reload the plugin configuration.
If the issue persists, run: /mcp to check registered servers.
```

### If servers show `[ ] Timeout`:

The server is registered (tools appear in your tool list) but is not responding to calls. Suggest:

```
One or more servers are registered but not responding.
This may indicate a temporary service issue or network timeout.

Try:
1. Restart your Claude Code or Cowork session
2. Re-run /bettercallclaude:setup to check again
3. If the HTTP service health check failed, the service may be temporarily unavailable
```

### If health check failed:

```
The HTTP MCP service at mcp.bettercallclaude.ch is not reachable.

Possible causes:
- No internet connection
- DNS resolution failure (try: nslookup mcp.bettercallclaude.ch)
- Firewall blocking HTTPS on port 443
- Service temporarily unavailable (check again in a few minutes)

Workaround: Switch to local mode with /bettercallclaude:setup --local
```

### If ollama is not connected:

The ollama server runs locally and does not depend on the HTTP service. Suggest:

```
The ollama privacy classifier is not connected.
This server requires the plugin's bundled files. Try:
1. Restart Claude Code or Cowork
2. Verify the plugin is installed: claude plugin list
3. Check that Node.js 18+ is available: node --version
```

## Step 5: Handle Flags

### `--local` flag

Switch the 5 HTTP servers to local stdio transport by registering user-scoped overrides. This requires Node.js 18+ and the plugin's bundled server files.

**Step 5a: Check Node.js**

```bash
node --version
```

Require >= 18.0.0. If not found or too old, stop and tell the user Node.js 18+ is required for local mode.

**Step 5b: Locate server bundles**

```bash
SERVER_DIR=""
for candidate in \
  "${CLAUDE_PLUGIN_ROOT:-}/mcp-servers" \
  "$(find ~/.claude/plugins -type d -name 'mcp-servers' -path '*bettercallclaude*' 2>/dev/null | head -1)" \
  "./mcp-servers" \
  "./bettercallclaude/mcp-servers"; do
  if [ -n "$candidate" ] && [ -f "$candidate/entscheidsuche/dist/index.js" ]; then
    SERVER_DIR="$candidate"
    break
  fi
done
echo "SERVER_DIR=$SERVER_DIR"
```

If `SERVER_DIR` is empty, tell the user the plugin's server bundles could not be found.

**Step 5c: Register stdio servers at user scope**

For each of the 5 servers, run:

```bash
claude mcp add bettercallclaude-entscheidsuche -s user -- node "$SERVER_DIR/entscheidsuche/dist/index.js"
claude mcp add bettercallclaude-bge-search -s user -- node "$SERVER_DIR/bge-search/dist/index.js"
claude mcp add bettercallclaude-legal-citations -s user -- node "$SERVER_DIR/legal-citations/dist/index.js"
claude mcp add bettercallclaude-fedlex-sparql -s user -- node "$SERVER_DIR/fedlex-sparql/dist/index.js"
claude mcp add bettercallclaude-onlinekommentar -s user -- node "$SERVER_DIR/onlinekommentar/dist/index.js"
```

User-scoped servers override the plugin's HTTP defaults. Tell the user:

```
Switched to local transport. 5 servers registered at user scope.
Restart Claude Code or Cowork to apply the change.
Re-run /bettercallclaude:setup to verify.

To switch back to HTTP: /bettercallclaude:setup --restore-http
```

### `--restore-http` flag

Remove user-scoped stdio overrides, restoring the plugin's HTTP defaults:

```bash
claude mcp remove bettercallclaude-entscheidsuche -s user
claude mcp remove bettercallclaude-bge-search -s user
claude mcp remove bettercallclaude-legal-citations -s user
claude mcp remove bettercallclaude-fedlex-sparql -s user
claude mcp remove bettercallclaude-onlinekommentar -s user
```

Tell the user:

```
Restored HTTP transport. User-scoped overrides removed.
Restart Claude Code or Cowork to apply the change.
Re-run /bettercallclaude:setup to verify.
```

## Step 6: Backend Error Diagnostics

If a server connects but returns errors during use, consult this diagnostic guide:

| Error Pattern | Likely Cause | Resolution |
|---------------|-------------|------------|
| HTTP 429 or "rate limited" | Too many requests (limit: 60 req/min per IP) | Wait a moment and retry. Reduce request frequency. |
| SPARQL endpoint timeout or HTTP 5xx from fedlex-sparql | Fedlex service (`fedlex.data.admin.ch`) is temporarily unavailable | Retry later. The server has built-in retry logic (3 attempts, 2s delay). This is an external service issue. |
| "ECONNREFUSED" or "ENOTFOUND" in local mode | Server cannot reach the external API | Check internet connection. Verify DNS resolution for the relevant domain. |
| Connection works but no search results | Server is healthy but the query returned no matches | Try broader search terms or different parameters. |

## Notes

- MCP servers are required for live database access (court decisions, legislation, citation verification)
- Without MCP servers, BetterCallClaude operates in **reduced mode** using built-in Swiss law knowledge
- Reduced mode cannot search live databases, verify citation existence, or access current legislation
- All servers are self-contained and require no API keys or external accounts
- The HTTP service is rate-limited to 60 requests per minute per IP address
- The ollama privacy classifier always runs locally to keep sensitive data on your machine

## User Query

$ARGUMENTS
