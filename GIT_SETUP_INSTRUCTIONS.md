# Git Setup Instructions for BetterCallClaude

Two methods to initialize and push the repository to GitHub.

---

## Method 1: Automated Script (Recommended)

### Step 1: Make Script Executable
```bash
cd /Users/federicocesconi/Dev/BetterCallClaude
chmod +x git-setup.sh
```

### Step 2: Run Script
```bash
./git-setup.sh
```

The script will:
1. ✅ Initialize git repository
2. ✅ Create .gitignore
3. ✅ Add all files
4. ✅ Create comprehensive commit message
5. ✅ Add GitHub remote
6. ✅ Push to https://github.com/fedec65/BetterCallClaude

---

## Method 2: Manual Steps

### Step 1: Navigate to Project
```bash
cd /Users/federicocesconi/Dev/BetterCallClaude
```

### Step 2: Initialize Git (if not already done)
```bash
git init
git branch -M main
```

### Step 3: Configure Git User (if needed)
```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Step 4: Create .gitignore
```bash
cat > .gitignore << 'EOF'
# macOS
.DS_Store

# IDEs
.vscode/
.idea/
*.swp

# Node.js (for future MCP servers)
node_modules/
*.log

# Environment variables
.env
.env.local

# Build artifacts
dist/
build/

# MCP Server specific
mcp-servers/*/node_modules/
mcp-servers/*/dist/
mcp-servers/*/.env
EOF
```

### Step 5: Add All Files
```bash
git add .
```

### Step 6: Review Status
```bash
git status
```

### Step 7: Create Commit
```bash
git commit -m "Initial commit: BetterCallClaude Framework v1.0.0-alpha

Foundation Phase Complete (100%)

Core Framework:
- Legal Principles and Swiss Law Configuration
- Citation and Symbol System
- Multi-lingual support (DE/FR/IT/EN)

Personas (3/3):
- Legal Researcher: BGE research, statute interpretation
- Case Strategist: Litigation strategy, risk assessment
- Legal Drafter: Contract drafting, document generation

Modes (3/3):
- Federal Law: Swiss federal statutes and BGE
- Cantonal Law: 6 cantons (ZH/BE/GE/BS/VD/TI)
- Multi-Lingual: Native DE/FR/IT/EN reasoning

MCP Specifications (2/2):
- Entscheidsuche: Court decision search spec
- Legal Citations: Citation verification spec

Documentation:
- Comprehensive README
- Complete installation guide (INSTALLATION.md)
- Detailed usage guide (USAGE_GUIDE.md)
- Development roadmap (IMPLEMENTATION_STATUS.md)

Target Users: Swiss lawyers and legal professionals
Framework: Claude Code v1.0+

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 8: Add GitHub Remote
```bash
git remote add origin https://github.com/fedec65/BetterCallClaude.git
```

### Step 9: Verify Remote
```bash
git remote -v
```

Expected output:
```
origin  https://github.com/fedec65/BetterCallClaude.git (fetch)
origin  https://github.com/fedec65/BetterCallClaude.git (push)
```

### Step 10: Push to GitHub
```bash
git push -u origin main
```

---

## Verification

### Check GitHub Repository

Visit: https://github.com/fedec65/BetterCallClaude

Verify:
- ✅ All files present
- ✅ README.md displays correctly
- ✅ Directory structure intact
- ✅ Commit message accurate

### Expected File Structure on GitHub

```
BetterCallClaude/
├── README.md
├── INSTALLATION.md
├── USAGE_GUIDE.md
├── IMPLEMENTATION_STATUS.md
├── IMPLEMENTATION_COMPLETE.md
├── HANDOFF_SUMMARY.md
├── GIT_SETUP_INSTRUCTIONS.md
├── git-setup.sh
├── .gitignore
│
├── .claude/
│   ├── BETTERASK.md
│   ├── LEGAL_PRINCIPLES.md
│   ├── LEGAL_SYMBOLS.md
│   ├── SWISS_LAW_CONFIG.md
│   │
│   ├── personas/
│   │   ├── PERSONA_Legal_Researcher.md
│   │   ├── PERSONA_Case_Strategist.md
│   │   └── PERSONA_Legal_Drafter.md
│   │
│   ├── modes/
│   │   ├── MODE_Federal_Law.md
│   │   ├── MODE_Cantonal_Law.md
│   │   └── MODE_Multi_Lingual.md
│   │
│   └── mcp/
│       ├── MCP_Entscheidsuche.md
│       └── MCP_Legal_Citations.md
│
├── mcp-servers/ (placeholder for Phase 2)
├── docs/ (placeholder)
├── examples/ (placeholder)
└── version-manager/ (placeholder)
```

---

## Troubleshooting

### Issue: Repository Already Exists

If you get "remote origin already exists":
```bash
git remote remove origin
git remote add origin https://github.com/fedec65/BetterCallClaude.git
```

### Issue: Push Rejected

If push is rejected (repository not empty):
```bash
# WARNING: Only if you want to overwrite remote
git push -u origin main --force

# OR: Pull and merge first
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Issue: Authentication Failed

GitHub requires personal access token for HTTPS:

1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo` (all)
4. Copy token
5. Use token as password when pushing

**OR** use SSH instead:
```bash
git remote set-url origin git@github.com:fedec65/BetterCallClaude.git
git push -u origin main
```

---

## Next Steps After Push

### 1. Repository Settings

Visit: https://github.com/fedec65/BetterCallClaude/settings

Configure:
- **Description**: "Legal Intelligence Framework for Swiss Lawyers | Claude Code Framework"
- **Topics**: swiss-law, legal-tech, claude-code, ai, legal-ai, switzerland
- **Website**: (your documentation site, if any)

### 2. Add License

Recommended licenses for open source legal tech:
- **MIT License**: Permissive, widely used
- **Apache 2.0**: Permissive with patent grant
- **GPL v3**: Copyleft (derivatives must be open source)

```bash
# Example: Add MIT License
curl https://raw.githubusercontent.com/licenses/license-templates/master/templates/mit.txt > LICENSE
# Edit LICENSE file with your name and year
git add LICENSE
git commit -m "Add MIT License"
git push
```

### 3. Enable GitHub Pages (Optional)

For documentation hosting:

1. Settings → Pages
2. Source: Deploy from branch
3. Branch: `main`, folder: `/docs` or `/ (root)`
4. Save

Documentation will be available at:
https://fedec65.github.io/BetterCallClaude/

### 4. Create Release

```bash
git tag -a v1.0.0-alpha -m "Foundation Phase Complete - MVP v1.0.0-alpha"
git push origin v1.0.0-alpha
```

Then on GitHub:
1. Releases → Draft a new release
2. Choose tag: v1.0.0-alpha
3. Title: "v1.0.0-alpha - Foundation Phase Complete"
4. Description: (copy from IMPLEMENTATION_COMPLETE.md)
5. Check "This is a pre-release"
6. Publish release

### 5. README Badges (Optional)

Add to top of README.md:

```markdown
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0--alpha-orange.svg)](https://github.com/fedec65/BetterCallClaude/releases)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-v1.0+-purple.svg)](https://claude.ai)
[![Swiss Law](https://img.shields.io/badge/Swiss%20Law-CH-red.svg)](https://www.admin.ch)
```

### 6. Community Setup

**GitHub Discussions**: Enable for Q&A and community

**Issue Templates**: Create templates for:
- Bug reports
- Feature requests
- Documentation improvements

**Contributing Guidelines**: Add CONTRIBUTING.md

**Code of Conduct**: Add CODE_OF_CONDUCT.md

### 7. Share with Community

Announce on:
- LinkedIn (Swiss legal tech groups)
- Twitter/X (#LegalTech #SwissLaw #AI)
- Legal tech forums
- Swiss bar associations (if appropriate)

---

## Quick Commands Reference

```bash
# Check repository status
git status

# View commit history
git log --oneline

# View remote URL
git remote -v

# Pull latest changes
git pull origin main

# Push changes
git push origin main

# Create new branch
git checkout -b feature/your-feature

# Switch back to main
git checkout main
```

---

## Support

If you encounter issues:

1. **Git Issues**: https://git-scm.com/doc
2. **GitHub Help**: https://docs.github.com
3. **Project Issues**: https://github.com/fedec65/BetterCallClaude/issues

---

**Created**: 2025-01-12
**Framework Version**: v1.0.0-alpha
**Repository**: https://github.com/fedec65/BetterCallClaude
