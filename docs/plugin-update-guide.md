# Claude Cowork Plugin Update Issue: Pro Plan GitHub-Synced Marketplaces

**Last Updated:** April 2, 2026  
**Affected Users:** Claude Pro plan users with GitHub-synced personal marketplaces  
**Platforms:** macOS, Windows, Linux  
**Status:** Known issue, workaround available

---

## What Happened?

If you've noticed that the **"Update" button has disappeared** from your GitHub-synced marketplace plugins in Claude Cowork, you're not alone. This is a confirmed issue affecting Pro plan users following the February 2026 Cowork platform restructuring.

### Key Changes (February 2026 Update)

- **Organization Settings removed from Pro plans**: The "Update" button for GitHub-synced marketplaces was moved to **Organization Settings > Plugins**, which is **only available on Team and Enterprise plans**
- **UI restructuring**: The plugin management interface was consolidated into the "Customize" menu, but the sync controls didn't make the transition for Pro users
- **Underlying sync bug**: Even when the Update button was visible, it wasn't properly executing `git pull` (see [Issue #41885](https://github.com/anthropics/claude-code/issues/41885))

---

## Who Is Affected?

✅ **You ARE affected if:**
- You're on a **Claude Pro plan** (not Team/Enterprise)
- You're using a **GitHub-synced personal marketplace** (like "Bettercallclaude")
- You previously saw an "Update" button but it's now missing
- Your plugins aren't reflecting the latest changes from your GitHub repository

❌ **You are NOT affected if:**
- You're on a **Team or Enterprise plan** (use Organization Settings > Plugins)
- You're using **manual/ZIP-upload marketplaces** (update by re-uploading with the same name)
- You're using **Anthropic's official public marketplaces**

---

## Why This Happened

### The Technical Issue

When you connect a GitHub repository as a marketplace:

1. Claude performs an initial `git clone` of your repository
2. **The problem**: The auto-sync mechanism runs `git fetch` but **never runs `git pull`**
3. Result: Your local clone stays frozen at the initial commit, even after clicking "Update"

This bug exists in both:
- Claude Desktop (Cowork interface)
- Claude Code CLI plugin system

---

## Platform-Specific File Locations

### macOS Path
```
~/Library/Application Support/Claude/local-agent-mode-sessions/
```

### Windows Path
```
%APPDATA%\Claude\local-agent-mode-sessions\
```
Full path:
```
C:\Users\[YourUsername]\AppData\Roaming\Claude\local-agent-mode-sessions\
```

### Linux Path
```
~/.config/Claude/local-agent-mode-sessions/
```

---

## Workaround 1: Manual Git Pull

Force-update your marketplace by manually pulling the latest changes.

### For macOS Users

Open Terminal and run:

```bash
# Navigate to the Claude Cowork marketplace cache
cd ~/Library/Application\ Support/Claude/local-agent-mode-sessions/

# Find your session (most recent directory)
ls -lt | head -n 10

# Navigate into the session and marketplace (replace with your actual paths)
cd {session-id}/{sub-id}/cowork_plugins/marketplaces/Bettercallclaude/

# Pull the latest changes from GitHub
git pull origin main

# Restart Claude Desktop to see updates
```

**Find your marketplace automatically:**
```bash
find ~/Library/Application\ Support/Claude -name "Bettercallclaude" -type d 2>/dev/null
```

---

### For Windows Users (PowerShell)

Open PowerShell and run:

```powershell
# Navigate to the Claude Cowork marketplace cache
cd $env:APPDATA\Claude\local-agent-mode-sessions\

# Find your session (most recent directory)
Get-ChildItem | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# Navigate into the session and marketplace (replace with your actual paths)
cd .\{session-id}\{sub-id}\cowork_plugins\marketplaces\Bettercallclaude\

# Pull the latest changes from GitHub
git pull origin main

# Restart Claude Desktop to see updates
```

**Find your marketplace automatically:**
```powershell
Get-ChildItem -Path $env:APPDATA\Claude -Recurse -Filter "Bettercallclaude" -Directory -ErrorAction SilentlyContinue
```

---

### For Windows Users (Command Prompt)

Open Command Prompt (CMD) and run:

```cmd
# Navigate to the Claude Cowork marketplace cache
cd %APPDATA%\Claude\local-agent-mode-sessions\

# List directories sorted by date (newest first)
dir /o-d

# Navigate into the session and marketplace (replace with your actual paths)
cd {session-id}\{sub-id}\cowork_plugins\marketplaces\Bettercallclaude\

# Pull the latest changes from GitHub
git pull origin main

# Restart Claude Desktop to see updates
```

**Find your marketplace automatically:**
```cmd
dir /s /b %APPDATA%\Claude\*Bettercallclaude*
```

---

### For Linux Users

Open Terminal and run:

```bash
# Navigate to the Claude Cowork marketplace cache
cd ~/.config/Claude/local-agent-mode-sessions/

# Find your session (most recent directory)
ls -lt | head -n 10

# Navigate into the session and marketplace
cd {session-id}/{sub-id}/cowork_plugins/marketplaces/Bettercallclaude/

# Pull the latest changes
git pull origin main

# Restart Claude Desktop to see updates
```

**Find your marketplace automatically:**
```bash
find ~/.config/Claude -name "Bettercallclaude" -type d 2>/dev/null
```

---

## Workaround 2: Remove and Re-add Marketplace

This forces a fresh clone with the latest commits. **Works the same on all platforms:**

1. Open Claude Desktop
2. Go to **Customize → Plugins**
3. Find your GitHub-synced marketplace (e.g., "Bettercallclaude")
4. Click the **menu (⋯)** → **Remove**
5. Click **+ → Add from GitHub**
6. Re-enter your repository URL and reconnect
7. Your marketplace will re-appear with the latest commits

**Pro tip:** If you have automatic sync enabled in your GitHub workflow settings, you may need to re-enable it after re-adding.

---

## Workaround 3: Use Claude Code CLI

If you use the Claude Code CLI tool:

### macOS/Linux:
```bash
cd ~/.claude/plugins/marketplaces/Bettercallclaude/
git pull origin main
claude plugin update adversarial-analysis@Bettercallclaude
```

### Windows:
```powershell
cd $env:USERPROFILE\.claude\plugins\marketplaces\Bettercallclaude\
git pull origin main
claude plugin update adversarial-analysis@Bettercallclaude
```

**Note:** The CLI has the same underlying bug, but manual git pull works.

---

## How to Verify Your Update Worked

After applying a workaround:

1. **Check the "Last updated" timestamp**: In Customize → Skills, click on any skill. Look for the "Last updated" field in the right panel.

2. **Compare with GitHub**: Check that the commit hash in your local clone matches your GitHub repository's latest commit:

**macOS/Linux:**
```bash
git log --oneline -1
```

**Windows:**
```powershell
git log --oneline -1
```

3. **Test new functionality**: If you recently added new skills or modified existing ones, verify those changes appear in the skill description.

---

## When Will This Be Fixed?

Anthropic has not provided an ETA. Track these GitHub issues:
- [Issue #41885](https://github.com/anthropics/claude-code/issues/41885) (Cowork/Desktop)
- [Issue #41871](https://github.com/anthropics/claude-code/issues/41871) (CLI)

---

## FAQ

**Q: Will I lose my plugins if I remove and re-add the marketplace?**
A: No. Your skills are stored in the repository. Removing only removes the local cache.

**Q: Will upgrading to Team plan solve this?**
A: Yes. Team/Enterprise plans have Organization Settings > Plugins. The underlying bug may still exist though.

**Q: I'm on Windows but git isn't recognized**
A: Install Git for Windows from git-scm.com, or use Git Bash instead of Command Prompt.

**Q: Do I need to do this every time I update my GitHub repo?**
A: Yes, until Anthropic fixes the auto-sync bug.

---

## Quick Reference

### macOS Commands Summary
```bash
# Find marketplace
find ~/Library/Application\ Support/Claude -name "Bettercallclaude" -type d 2>/dev/null

# Navigate and update
cd [path-found-above]
git pull origin main

# Restart: Cmd + Q, then reopen
```

### Windows Commands Summary
```powershell
# Find marketplace (PowerShell)
Get-ChildItem -Path $env:APPDATA\Claude -Recurse -Filter "Bettercallclaude" -Directory

# Or CMD
dir /s /b %APPDATA%\Claude\*Bettercallclaude*

# Navigate and update
cd [path-found-above]
git pull origin main

# Restart: Close window, quit from system tray, reopen
```

---

*Document version: 1.2*  
*Last updated: April 2, 2026*
