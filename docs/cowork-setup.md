# Setting Up BetterCallClaude in Claude Cowork

This guide walks you through installing BetterCallClaude in Claude Cowork (Desktop) using the GUI. The entire process takes about two minutes.

## Prerequisites

- Claude Desktop with Cowork access (Max plan)

## Step-by-Step Installation

### 1. Open Cowork

![Open Cowork](images/cowork-setup/01-open-cowork.png)

Open Claude Desktop and switch to the **Cowork** tab.

### 2. Open Customize

![Click Customize](images/cowork-setup/02-click-customize.png)

Click **CUSTOMIZE** in the top-left corner of the sidebar.

### 3. Browse Plugins

![Browse Plugins](images/cowork-setup/03-browse-plugins.png)

Click **Browse plugins** at the bottom of the Customize panel.

### 4. Switch to Personal Tab

![Click Personal](images/cowork-setup/04-click-personal.png)

Click the **PERSONAL** tab (not "By Anthropic & Partners").

### 5. Add a New Marketplace

![Click Plus](images/cowork-setup/05-click-plus.png)

Click the **+** button next to "Local uploads".

### 6. Select "Add Marketplace from GitHub"

![Add Marketplace from GitHub](images/cowork-setup/06-add-marketplace-github.png)

Choose **ADD MARKETPLACE FROM GITHUB** from the dropdown.

### 7. Enter Repository and Sync

![Enter repo and sync](images/cowork-setup/07-enter-repo-sync.png)

Type `fedec65/bettercallclaude` and click **Sync**.

### 8. Install the Plugin

![Click Install](images/cowork-setup/08-click-install.png)

Click **Install** on the BetterCallClaude plugin card.

### 9. Accept MCP Servers

![Click Continue](images/cowork-setup/09-click-continue.png)

A dialog lists the MCP servers the plugin will configure. Only `bettercallclaude-ollama` runs locally (for privacy classification) -- the other five connect via HTTP to hosted servers. Click **Continue**.

### 10. Verify Installation

![Click Manage](images/cowork-setup/10-click-manage.png)

The plugin is now installed. Click **Manage** to explore commands, skills, and agents.

---

## Verifying MCP Connectors

### 11. Open Connectors

![Click Connectors](images/cowork-setup/11-click-connectors.png)

In the plugin detail view, click **Connectors** in the left sidebar.

### 12. Check All 6 Connectors

![Check Connectors](images/cowork-setup/12-check-connectors.png)

Verify that all 6 connectors are listed:

- **bettercallclaude-entscheidsuche** (CUSTOM) -- Swiss court decision search
- **bettercallclaude-bge-search** (CUSTOM) -- Federal Supreme Court decisions
- **bettercallclaude-legal-citations** (CUSTOM) -- Citation verification
- **bettercallclaude-fedlex-sparql** (CUSTOM) -- Federal legislation database
- **bettercallclaude-onlinekommentar** (CUSTOM) -- Legal commentaries
- **bettercallclaude-ollama** -- Local privacy classification

### 13. Set Tool Permissions

![Always Allow](images/cowork-setup/13-always-allow.png)

Click each connector and ensure **Always allow** is set for its tools. This lets BetterCallClaude query Swiss Confederation databases without prompting for permission on every request.

### 14. Ollama (Optional)

![Ollama Local](images/cowork-setup/14-ollama-local.png)

The ollama connector runs locally via stdio. If you have [Ollama](https://ollama.com) installed on your computer, the privacy classifier is available for Anwaltsgeheimnis (attorney-client privilege) detection. If you don't have Ollama, this connector shows as disconnected -- that's fine, BetterCallClaude works fully without it.

---

## You're Ready!

Start a new Cowork task and try a command:

```
/bettercallclaude:legal What are the requirements for a valid non-compete clause under Art. 340 OR?

/bettercallclaude:research Art. 97 OR contractual liability precedents

/bettercallclaude:help
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| GitHub sync fails in the GUI | Use the terminal instead: open Cowork's built-in terminal and run `claude plugin marketplace add fedec65/bettercallclaude` |
| Connectors not showing after install | Restart Cowork |
| MCP servers not responding | Run `/bettercallclaude:setup` to check server health |
| Want to use local servers instead of HTTP | Run `/bettercallclaude:setup --local` (requires Node.js 18+) |

For the full installation guide (CLI, Windows, team setup, developer install), see [INSTALL.md](INSTALL.md).
