# BetterCallClaude Installation Guide

**Version 3.1.0** -- Swiss Legal Intelligence Plugin for Claude Code and Cowork Desktop

This guide covers installation, configuration, and verification for both platforms.

---

## Contents

1. [Before You Begin](#1-before-you-begin)
2. [Claude Code CLI Installation](#2-claude-code-cli-installation)
3. [Cowork Desktop Installation](#3-cowork-desktop-installation)
4. [Team Setup](#4-team-setup)
5. [Manual / Developer Installation](#5-manual--developer-installation)
6. [MCP Server Reference](#6-mcp-server-reference)
7. [Troubleshooting](#7-troubleshooting)
8. [Upgrading and Uninstalling](#8-upgrading-and-uninstalling)

---

## 1. Before You Begin

### Prerequisites

| Requirement | Details |
|-------------|---------|
| **Claude Code CLI** or **Cowork Desktop** | Latest version of either platform |
| **Node.js** | Version 18 or later (only required for `--local` mode or the ollama privacy classifier) |

No Python installation, API keys, or external accounts are required. The 5 main MCP servers connect via HTTP and need no local setup.

### Which Platform Are You Using?

- **Claude Code CLI**: A command-line tool you run in your terminal (macOS, Linux, Windows). If you installed Claude Code with `npm`, `brew`, or one of the Anthropic install scripts, you are using the CLI. Go to [Part 2](#2-claude-code-cli-installation).

- **Cowork Desktop**: A desktop application with a graphical interface that includes Claude Code in a sandboxed virtual machine. If you downloaded Cowork from Anthropic's website and it runs as a standalone app with a sidebar, you are using Cowork. Go to [Part 3](#3-cowork-desktop-installation).

- **Developer / contributor**: If you want to build from source or run the plugin from a local clone. Go to [Part 5](#5-manual--developer-installation).

---

## 2. Claude Code CLI Installation

### 2.1 Install the Plugin

Open your terminal and run:

```
claude plugin marketplace add fedec65/bettercallclaude
claude plugin install bettercallclaude@bettercallclaude-marketplace
```

### 2.2 Verify the Installation

1. Restart Claude Code (quit and reopen).
2. Run the version command:

   ```
   /bettercallclaude:version
   ```

   You should see a status report listing 18 commands, 19 agents, 10 skills, and 6 MCP servers (5 HTTP + 1 local).

3. Run the setup command to check MCP server connectivity:

   ```
   /bettercallclaude:setup
   ```

   This probes all 6 MCP servers and displays a status table with transport type (HTTP or Local) for each server.

4. Test a command:

   ```
   /bettercallclaude:help
   ```

### 2.3 Windows Notes

Claude Code on Windows requires [Git for Windows](https://git-scm.com/downloads/win). Install Git first, then install Claude Code using one of these methods:

**PowerShell:**

```powershell
irm https://claude.ai/install.ps1 | iex
```

**CMD:**

```batch
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

**WinGet:**

```powershell
winget install Anthropic.ClaudeCode
```

After Claude Code is installed, install the plugin using the same two commands from Section 2.1:

```
claude plugin marketplace add fedec65/bettercallclaude
claude plugin install bettercallclaude@bettercallclaude-marketplace
```

You can launch `claude` from PowerShell, CMD, or Git Bash. Administrator privileges are not required.

**WSL users**: Both WSL 1 and WSL 2 are supported. Inside your WSL terminal, install Claude Code with `curl -fsSL https://claude.ai/install.sh | bash`, then install the plugin as above.

**Git Bash not found?** If Claude Code cannot locate your Git Bash installation, add this to your `settings.json`:

```json
{ "env": { "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe" } }
```

### 2.4 Linux Notes

Install Claude Code using the official install script:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Then install the plugin with the same two commands from Section 2.1. No platform-specific adjustments are needed.

---

## 3. Cowork Desktop Installation

### 3.1 Install the Plugin

Open Cowork's built-in terminal (click **Terminal** in the bottom bar) and run:

```
claude plugin marketplace add fedec65/bettercallclaude
claude plugin install bettercallclaude@bettercallclaude-marketplace
```

**Why the terminal?** The Cowork GUI "Add marketplace from GitHub" dialog has a known networking issue that prevents it from reaching GitHub from within the sandboxed VM ([#26951](https://github.com/anthropics/claude-code/issues/26951), [#28125](https://github.com/anthropics/claude-code/issues/28125), [#28853](https://github.com/anthropics/claude-code/issues/28853)). The terminal method works reliably.

### 3.2 That's It -- HTTP Servers Work Immediately

Five of the six MCP servers connect via HTTP to a hosted service at `https://mcp.bettercallclaude.ch`. HTTP requests work through the Cowork VM sandbox with zero additional configuration.

The sixth server (ollama privacy classifier) runs locally using the plugin's bundled files and works inside the VM.

No Node.js installation, no file copying, no config editing.

### 3.3 Verify the Installation

1. Restart Cowork (or open a new session).
2. Run the version command:

   ```
   /bettercallclaude:version
   ```

   You should see 18 commands, 19 agents, 10 skills, and 6 MCP servers.

3. Run the setup command to check connectivity:

   ```
   /bettercallclaude:setup
   ```

   All 5 HTTP servers should show as connected. The ollama server should also show as connected (Local transport).

4. Test a research command:

   ```
   /bettercallclaude:research Art. 97 OR contractual liability
   ```

### 3.4 Why HTTP Transport

Cowork Desktop runs inside a sandboxed virtual machine. In previous versions, MCP servers used stdio transport (local Node.js processes), but the VM sandbox prevented these child processes from making outbound network requests to Swiss legal databases. This required a complex multi-step workaround to install servers on the host machine outside the VM.

With HTTP transport, the MCP client makes standard HTTPS requests to the hosted service. HTTPS works through the VM sandbox the same way any web request does. No workaround is needed.

### 3.5 Advanced: Switch to Local Transport

For lower latency or offline capability, power users can switch the 5 HTTP servers to local stdio transport:

```
/bettercallclaude:setup --local
```

This requires:
- Node.js 18+ installed and accessible
- The plugin's bundled server files (included with the plugin)

Local servers are registered at user scope and override the plugin's HTTP defaults. To switch back:

```
/bettercallclaude:setup --restore-http
```

### 3.6 Working Without MCP Servers

If MCP server configuration is not possible or not needed, BetterCallClaude still works in **reduced mode**:

- All 18 commands, 19 agents, and 10 skills remain fully functional.
- Legal analysis, strategy, drafting, translation, and adversarial analysis work using Claude's built-in Swiss law knowledge.
- The privacy classification tool (ollama server) works inside the VM.

What reduced mode cannot do:

- Search live court decision databases (entscheidsuche, bge-search).
- Verify citation existence against live databases.
- Query current federal legislation via SPARQL (fedlex-sparql).
- Access legal commentaries (onlinekommentar).

For many use cases (strategy development, document drafting, legal translation, adversarial analysis), reduced mode is fully sufficient.

---

## 4. Team Setup

To ensure every team member who clones your project repository gets prompted to install BetterCallClaude automatically, add the following to `.claude/settings.json` in your project root:

```json
{
  "extraKnownMarketplaces": {
    "bettercallclaude-marketplace": {
      "source": {
        "source": "github",
        "repo": "fedec65/bettercallclaude"
      }
    }
  }
}
```

Commit this file to your repository. When a team member opens the project with Claude Code or Cowork, they will be prompted to install the plugin.

MCP servers connect via HTTP by default, so no per-machine server configuration is needed. Team members only need to accept the plugin installation prompt (or run the two `claude plugin` commands manually).

---

## 4.1 Starting a New Case

After installing BetterCallClaude, create a project directory for each case and populate it with the case template:

1. Create a directory for the case:

   ```
   mkdir ~/cases/keller-v-techcorp
   ```

2. Copy the template into the directory as `CLAUDE.md`:

   ```
   cp docs/templates/case-claude-md.md ~/cases/keller-v-techcorp/CLAUDE.md
   ```

   If you installed from the marketplace (not a local clone), download the template from GitHub:

   ```
   curl -fsSL https://raw.githubusercontent.com/fedec65/bettercallclaude/main/docs/templates/case-claude-md.md \
     -o ~/cases/keller-v-techcorp/CLAUDE.md
   ```

3. Open `CLAUDE.md` in a text editor and fill in the `[REPLACE: ...]` placeholders: matter title, jurisdiction, canton, parties, key dates, applicable statutes, and privacy mode.

4. Start Claude in that directory:

   ```
   cd ~/cases/keller-v-techcorp
   claude
   ```

5. The briefing coordinator reads your `CLAUDE.md` on startup and skips questions you have already answered, going directly to the gaps that remain.

---

## 5. Manual / Developer Installation

### 5.1 Run from a Local Clone

```bash
git clone https://github.com/fedec65/bettercallclaude.git
cd bettercallclaude
claude --plugin-dir bettercallclaude/
```

The `bettercallclaude/` subdirectory is the plugin root. It contains all agents, commands, skills, hooks, MCP server bundles, and the `.mcp.json` configuration.

### 5.2 Build MCP Servers from Source

The `mcp-servers-src/` directory contains TypeScript source for all six MCP servers. Pre-compiled bundles are included in `bettercallclaude/mcp-servers/*/dist/`, so building from source is only necessary if you are modifying server code.

```bash
# Install dependencies
npm install

# Compile TypeScript and bundle into bettercallclaude/mcp-servers/*/dist/
npm run build:bundle

# Run tests
npm test

# Create distributable plugin zip
npm run package

# Create .mcpb bundles for Claude Desktop
npm run build:mcpb
```

### 5.3 Repository Structure

```
bettercallclaude/              Plugin root (single source of truth)
  .claude-plugin/              Plugin manifest
  .mcp.json                    MCP server configuration (5 HTTP + 1 local)
  agents/                      19 agent definitions (markdown)
  commands/                    18 slash commands (markdown)
  skills/                      10 auto-activated skills (markdown)
  hooks/                       Privacy detection hook
  mcp-servers/                 Pre-compiled MCP server bundles (used for --local mode and ollama)
mcp-servers-src/               TypeScript source for MCP servers
  shared/                      Shared infrastructure (database, HTTP, NLP)
  entscheidsuche/              Swiss court decision search
  bge-search/                  Federal Supreme Court search
  legal-citations/             Citation verification and formatting
  fedlex-sparql/               Federal legislation via SPARQL
  onlinekommentar/             Legal commentaries
  ollama/                      Privacy classification (offline)
  integration-tests/           Cross-server integration tests
mcp-servers-http/              HTTP MCP service (deployed to Railway)
scripts/                       Build and installation scripts
docs/                          Documentation
```

---

## 6. MCP Server Reference

BetterCallClaude includes six MCP servers. Five connect via HTTP to a hosted service; one runs locally. All servers require no API keys or external accounts.

### Server Details

| Server | Description | Transport | External API |
|--------|-------------|-----------|--------------|
| **entscheidsuche** | Searches Swiss court decisions across federal and cantonal courts via entscheidsuche.ch. Supports keyword search, language filtering, and court-specific queries. | HTTP | entscheidsuche.ch |
| **bge-search** | Searches Federal Supreme Court (BGE/ATF/DTF) decisions. Supports keyword search, article reference filtering, date ranges, and section filtering. | HTTP | bger.ch |
| **legal-citations** | Validates citation format and existence. Converts citations between DE/FR/IT/EN formats (BGE/ATF/DTF). | HTTP | Partial (format validation is local; existence checks require network) |
| **fedlex-sparql** | Queries Swiss federal legislation via the Fedlex SPARQL endpoint. Retrieves statutes by SR number, searches legislation, finds related acts, gets article text. Has built-in retry logic (3 attempts, 2-second delay). | HTTP | fedlex.data.admin.ch |
| **onlinekommentar** | Searches Swiss legal commentaries (Kommentare). Finds scholarly analysis by article reference, keyword, or legislative act. | HTTP | onlinekommentar.ch |
| **ollama** | Privacy classification using offline regex patterns. Detects privileged (PRIVILEGED) and confidential (CONFIDENTIAL) content in German, French, and Italian. Does not require Ollama to be installed. | Local | None |

### How Servers Register

By default, the 5 main servers connect via HTTP to `https://mcp.bettercallclaude.ch`. This is configured in the plugin's `.mcp.json` file and works automatically on all platforms, including Cowork Desktop's sandboxed VM.

The ollama server runs locally via stdio using the plugin's bundled files.

To switch to local stdio transport for the 5 HTTP servers (requires Node.js 18+):

```
/bettercallclaude:setup --local
```

To switch back to HTTP:

```
/bettercallclaude:setup --restore-http
```

---

## 7. Troubleshooting

### Plugin Not Loading

1. Confirm the plugin is installed:

   ```
   claude plugin list
   ```

   You should see `bettercallclaude` in the output.

2. If not listed, re-run the installation commands:

   ```
   claude plugin marketplace add fedec65/bettercallclaude
   claude plugin install bettercallclaude@bettercallclaude-marketplace
   ```

3. Restart Claude Code or Cowork after installation.

### Commands Not Recognized

All BetterCallClaude commands use the `/bettercallclaude:` prefix. For example:

```
/bettercallclaude:help
/bettercallclaude:research Art. 97 OR
/bettercallclaude:version
```

If commands are not recognized after installation, restart Claude Code or Cowork.

### MCP Servers Not Connecting

1. **Check the HTTP service**: Run `/bettercallclaude:setup` to test connectivity. The setup command checks the health endpoint at `https://mcp.bettercallclaude.ch/health` and probes each server.

2. **Internet connection**: The 5 HTTP servers require internet access. Verify connectivity: `curl -sf https://mcp.bettercallclaude.ch/health`.

3. **DNS or firewall**: If the health check fails, check DNS resolution (`nslookup mcp.bettercallclaude.ch`) and ensure HTTPS on port 443 is not blocked.

4. **Rate limiting**: The HTTP service allows 60 requests per minute per IP. If you see HTTP 429 errors, wait a moment and retry.

5. **Switch to local mode**: If the HTTP service is persistently unreachable, switch to local transport: `/bettercallclaude:setup --local` (requires Node.js 18+).

6. **Ollama not connecting**: The ollama server runs locally and does not use the HTTP service. Ensure Node.js 18+ is available and restart Claude Code or Cowork.

### Cowork GUI Install Fails

The "Add marketplace from GitHub" dialog in Cowork has a known networking bug ([#26951](https://github.com/anthropics/claude-code/issues/26951), [#28125](https://github.com/anthropics/claude-code/issues/28125), [#28853](https://github.com/anthropics/claude-code/issues/28853)). Use the terminal method instead:

1. Open Cowork's built-in terminal (click **Terminal** in the bottom bar).
2. Run the two `claude plugin` commands from [Section 3.1](#31-install-the-plugin).

### SPARQL / Fedlex Timeout

The fedlex-sparql server queries `fedlex.data.admin.ch`, which is an external government service. Timeouts or HTTP 5xx errors indicate the Fedlex service is temporarily unavailable. The server has built-in retry logic (3 attempts with a 2-second delay). If the problem persists, try again later. This is not a plugin issue.

### Windows-Specific Issues

- **Git Bash path**: If Claude Code cannot find Git Bash, set the path in `settings.json`:

  ```json
  { "env": { "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe" } }
  ```

- **Execution policy**: If PowerShell blocks the install script, you may need to run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` first. This is a one-time Windows configuration.

- **WSL**: Both WSL 1 and WSL 2 are supported. Install Claude Code inside WSL using the bash install script, then install the plugin as normal.

---

## 8. Upgrading and Uninstalling

### Upgrading

To update to the latest version:

```
claude plugin update
```

After updating, run `/bettercallclaude:version` to confirm the new version number.

### Uninstalling

To remove the plugin:

```
claude plugin uninstall bettercallclaude
```

If you used `--local` mode, also remove the user-scoped server overrides:

```
/bettercallclaude:setup --restore-http
```

Or manually:

```
claude mcp remove bettercallclaude-entscheidsuche -s user
claude mcp remove bettercallclaude-bge-search -s user
claude mcp remove bettercallclaude-legal-citations -s user
claude mcp remove bettercallclaude-fedlex-sparql -s user
claude mcp remove bettercallclaude-onlinekommentar -s user
```

---

## Further Resources

- [Command Reference](command-reference.md) -- Full list of all commands with usage examples.
- [CONNECTORS.md](../CONNECTORS.md) -- Detailed MCP server API documentation.
- [README](../README.md) -- Project overview, component list, and quick start.
- [GitHub Issues](https://github.com/fedec65/bettercallclaude/issues) -- Report bugs or request features.

---

**BetterCallClaude v3.1.0** -- Swiss Legal Intelligence Plugin

All outputs produced by this plugin require professional lawyer review and validation before use. This tool assists legal professionals but does not replace professional judgment or the duty of care owed to clients.
