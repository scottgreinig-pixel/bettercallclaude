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

Attempt to call a tool from each of the 6 MCP servers to determine connectivity. For each server, try listing its available tools or calling a no-op endpoint:

| Server | Test Method |
|--------|-------------|
| bettercallclaude-entscheidsuche | Try calling any `search_decisions` or listing tools |
| bettercallclaude-bge-search | Try calling any `search_bge` or listing tools |
| bettercallclaude-legal-citations | Try calling any `validate_citation` or listing tools |
| bettercallclaude-fedlex-sparql | Try calling any `search_legislation` or listing tools |
| bettercallclaude-onlinekommentar | Try calling any `search_commentaries` or listing tools |
| bettercallclaude-ollama | Try calling any `ollama_check_status` or listing tools |

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
  ollama                    [x] Connected       Local

  HTTP Service: https://mcp.bettercallclaude.ch
  Health: OK / Unreachable
  Connected: X/6 servers
==============================================
```

Mark each server as `[x] Connected` or `[ ] Not connected` based on Step 2 results. Show `HTTP` or `Local` in the Transport column.

## Step 4: Provide Guidance Based on Results

### If all 6 servers are connected:

```
All MCP servers are operational. No action needed.
BetterCallClaude is running at full capability.
```

### If HTTP servers are not connected but health check passed:

The HTTP service is online but the servers are not registering. Suggest:

```
The HTTP service is healthy but servers are not connecting.
Try restarting Claude Code or Cowork to reload the plugin configuration.
If the issue persists, run: /mcp to check registered servers.
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
