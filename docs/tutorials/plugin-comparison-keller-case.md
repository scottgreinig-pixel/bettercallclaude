### # Two Plugins, One Case: BetterCallClaude vs. Anthropic Legal for Swiss Law
### This guide compares two Claude plugins — Anthropic's **Legal** plugin and **BetterCallClaude** — by applying both to the same Swiss employment law case. If you've read the [Employment Case Walkthrough](employment-case-walkthrough.md), you already know how BetterCallClaude handles the Keller v. AlphaFin AG wrongful termination matter. Here we show what happens when you try the same case with the generic Legal plugin, and explain why each tool fits different use cases.
### **Who this is for**: Lawyers choosing between plugins, legal operations teams evaluating tools, and plugin developers understanding the ecosystem.
### **Time to read**: 15-20 minutes
### ---
### ## The Anthropic Legal Plugin — What It Does Well
### Anthropic's [Legal plugin](https://github.com/anthropics/knowledge-work-plugins/tree/main/legal) is an AI-powered productivity tool designed for in-house legal teams at technology companies. It automates contract review, NDA screening, compliance workflows, legal briefings, and templated responses — all configurable to an organization's specific playbook and risk tolerances.
### The plugin provides five commands:
### | Command | Purpose |
### |---------|---------|
### | `/review-contract` | Review a contract clause by clause against your organization's negotiation playbook. Flags deviations as GREEN/YELLOW/RED and generates redline language. |
### | `/triage-nda` | Rapid pre-screening of incoming NDAs. Categorizes as GREEN (standard approval), YELLOW (counsel review), or RED (significant issues). |
### | `/vendor-check` | Look up existing agreements with a vendor across connected systems — NDAs, MSAs, DPAs, expiration dates, key terms. |
### | `/brief` | Generate contextual briefings: daily morning brief, topic research brief, or rapid incident brief. |
### | `/respond` | Generate templated responses for common inquiry types: data subject requests, discovery holds, vendor questions, NDA requests. |
### Beyond commands, the plugin includes six skills (contract-review, nda-triage, compliance, canned-responses, legal-risk-assessment, meeting-briefing) and integrates with corporate tools via MCP — Slack, Box, Egnyte, Microsoft 365, and Atlassian. The playbook system (`legal.local.md`) lets teams encode their standard contract positions, acceptable ranges, and escalation triggers so that reviews are consistent across the team.
### This is a well-designed plugin for its intended purpose: helping commercial counsel, product counsel, and compliance teams manage the high-volume, repetitive legal work that dominates in-house practice — contract review, NDA triage, vendor management, and stakeholder communication.
### ---
### ## Applying the Anthropic Legal Plugin to the Keller Case
### The Maria Keller wrongful termination case involves a software engineer terminated 21 days after reporting FINMA compliance gaps at AlphaFin AG (Zürich). She claims retaliatory dismissal under Art. 336 lit. d OR and seeks up to six months' salary in indemnity under Art. 336a. (For full case details, see the [Employment Case Walkthrough](employment-case-walkthrough.md).)
### Here is what happens when you attempt to use each Legal plugin command on this matter:
### ### `/review-contract` — Partial fit
### You could upload Maria's employment contract and ask the plugin to review it. The contract-review skill would flag clauses against your playbook — limitation of liability, IP ownership, term and termination. However, the plugin has no built-in knowledge of Swiss employment law (OR 335-336a). It cannot identify that the retroactive probation extension violates Art. 335b OR, because it evaluates contracts against your custom playbook, not against a specific jurisdiction's mandatory provisions. You would need to manually encode all Swiss employment law rules into `legal.local.md` before the review could catch Swiss-specific issues.
### **Result**: The plugin reviews the contract structure, but misses the jurisdiction-specific legal defects that are central to this case.
### ### `/triage-nda` — Not applicable
### NDA triage is designed for screening incoming non-disclosure agreements. The Keller case involves an employment dispute, not an NDA. This command has no relevance here.
### ### `/vendor-check` — Not applicable
### Vendor agreement lookup checks the status of vendor relationships across connected systems. An employment law matter is outside this command's scope.
### ### `/brief topic "wrongful termination Swiss law"` — General context only
### The brief command could generate a research briefing on wrongful termination under Swiss law. It draws on Claude's training data, which includes general knowledge of Swiss employment law. You would get a reasonable high-level overview of Art. 336 OR and the concept of missbräuchliche Kündigung.
### However, the briefing cannot:
### - Search the BGE database for specific precedents (BGE 136 III 513, BGE 125 III 70, etc.)
### - Verify whether cited decisions actually exist or have been overruled
### - Apply cantonal procedural rules (Zürich Arbeitsgericht, Schlichtungsverfahren)
### - Convert citations between DE/FR/IT formats (BGE/ATF/DTF)
### - Calculate court fees based on Zürich cantonal fee schedules
### **Result**: A useful starting point for understanding the legal landscape, but not a substitute for jurisdiction-specific research with verified citations.
### ### `/respond` — Generic letter only
### The respond command could draft a general response letter — for example, a formal objection to the termination. It uses your configured templates and applies a professional tone. But it cannot produce a Swiss court submission (Klageschrift) with ZPO-compliant structure: the Rechtsbegehren (prayer for relief), Sachverhalt (statement of facts), and Rechtliche Begründung (legal reasoning) sections that Swiss courts require. It also cannot insert verified BGE citations or apply the formal register expected by Swiss courts.
### **Result**: A generic business letter, not a court-ready legal document.
### ### Summary
### The Anthropic Legal plugin can provide general context for the Keller case — a high-level briefing on Swiss employment law, a structural review of the employment contract, and a templated response letter. These are useful starting points. But the plugin cannot execute the specialized workflow this case requires: live precedent research, citation verification, adversarial stress-testing, jurisdiction-specific strategy, and court-compliant document drafting.
### ---
### ## Applying BetterCallClaude to the Same Case
### BetterCallClaude handles the Keller case through a six-step pipeline, described in full in the [Employment Case Walkthrough](employment-case-walkthrough.md). Here is a brief recap of what each step produces, focusing on the five capabilities the Legal plugin lacks.
### ### 1. Live BGE/ATF/DTF database search
### The `/bettercallclaude:research` command activates the swiss-legal-researcher agent, which queries the bge-search, entscheidsuche, and fedlex-sparql MCP servers. For the Keller case, it returns four key precedents — BGE 136 III 513 (retaliatory dismissal elements), BGE 132 III 115 (indemnity calculation), BGE 134 III 108 (burden of proof), and BGE 125 III 70 (probation period rules) — each verified against live databases, not recalled from training data.
### ### 2. Swiss citation verification and cross-language conversion
### The `/bettercallclaude:cite` command verifies that each citation exists, confirms the correct volume/section/page, and converts between BGE (German), ATF (French), and DTF (Italian) formats. A Geneva lawyer working on the same case in French receives ATF 136 III 513 with French-language legal terminology automatically.
### ### 3. Three-agent adversarial analysis
### The `/bettercallclaude:adversarial` command runs three independent agents — an advocate who builds the strongest case for Maria, an adversary who identifies the employer's best defenses, and a judicial analyst who synthesizes both positions using Swiss Erwägung (consideration) methodology with probability estimates. The judicial analyst's synthesis concludes: favorable outcome 65-75%, expected indemnity 3-4 months' salary (CHF 37,500-50,000).
### ### 4. Jurisdiction-aware litigation strategy
### The `/bettercallclaude:strategy` command maps the full procedural pathway specific to the canton: written objection (Einsprache), conciliation at Friedensrichteramt Zürich (Schlichtungsverfahren), and if necessary, lawsuit at Arbeitsgericht Zürich. It calculates financial exposure using actual Zürich court fee schedules and recommends a settlement range based on cost-benefit analysis.
### ### 5. ZPO-compliant document drafting
### The `/bettercallclaude:draft` command produces a formal Klageschrift for the Arbeitsgericht Zürich, structured per ZPO requirements: Rechtsbegehren, Sachverhalt, Rechtliche Begründung, and Beweismittel, with proper citation format, formal register, and placeholder fields for the lawyer to complete.
### ### Privacy protection
### BetterCallClaude's PreToolUse hook detects Anwaltsgeheimnis (attorney-client privilege) indicators in German, French, and Italian before any external API call proceeds. The Anthropic Legal plugin has no equivalent privacy mechanism for privileged content.
### ---
### ## Side-by-Side Comparison
### | Aspect | Anthropic Legal | BetterCallClaude |
### |--------|----------------|------------------|
### | **Scope** | Generic — contracts, NDAs, compliance for in-house teams | Swiss-specific — all 26 cantons, federal and cantonal law |
### | **Languages** | English | DE, FR, IT, EN with legal terminology mapping |
### | **Data sources** | Claude's training data only | 5 live MCP servers (bge-search, entscheidsuche, legal-citations, fedlex-sparql, onlinekommentar) + Ollama for local inference |
### | **Agents** | 0 specialized agents | 19 specialized legal agents |
### | **Commands** | 5 (`/review-contract`, `/triage-nda`, `/vendor-check`, `/brief`, `/respond`) | 18 (research, strategy, draft, adversarial, briefing, workflow, etc.) |
### | **Skills** | 6 (contract-review, nda-triage, compliance, canned-responses, risk-assessment, meeting-briefing) | 10 (research, strategy, drafting, citations, jurisdictions, privacy, adversarial, compliance, data protection, briefing) |
### | **Precedent research** | No live search — relies on training data | BGE/ATF/DTF search with citation chain tracking and verification |
### | **Adversarial analysis** | No | Three-agent Erwägung methodology (advocate/adversary/judicial analyst) |
### | **Document drafting** | Generic templates via `/respond` | ZPO/CPC-compliant court submissions, contracts, legal opinions |
### | **Privacy protection** | No privilege detection | Anwaltsgeheimnis hook (Art. 321 StGB) — detects privileged content in DE/FR/IT before external API calls |
### | **Playbook system** | Yes — `legal.local.md` with standard positions, escalation triggers | No playbook system |
### | **Corporate tool integration** | Slack, Box, Egnyte, Microsoft 365, Atlassian | Swiss legal databases (BGE, entscheidsuche, Fedlex, Onlinekommentar) |
### | **Target users** | In-house commercial legal teams | Swiss lawyers and legal professionals |
### | **Cost** | Free | Free |
### | **License** | MIT | AGPL-3.0 |
### ---
### ## When to Use Which
### ### Use the Anthropic Legal plugin when:
### - You are an **in-house legal team** managing contracts, NDAs, and vendor agreements.
### - Your work is primarily **English-language commercial law** — SaaS agreements, data protection addenda, licensing terms.
### - You need **Slack/Jira/Box integration** for workflow automation — contract requests via Slack, matter tracking in Jira, playbooks stored in Box.
### - You want a **playbook-based review system** where your team's standard positions are encoded and consistently applied across all contract reviews.
### - Your practice does not require jurisdiction-specific legal research or court-level document drafting.
### ### Use BetterCallClaude when:
### - You are a **Swiss lawyer or legal professional** working with Swiss federal or cantonal law.
### - Your work involves **BGE precedent research**, Swiss court procedures, or multi-lingual legal analysis (DE/FR/IT).
### - You need **court-ready documents** — Klageschriften, Klageantworten, Berufungen — structured per ZPO requirements with verified Swiss citations.
### - You handle matters that benefit from **adversarial stress-testing** — the three-agent methodology reveals weaknesses before opposing counsel does.
### - You work across **multiple Swiss language regions** and need citations and terminology that adapt automatically (BGE/ATF/DTF, OR/CO, ZPO/CPC).
### ### Use both together:
### The two plugins are complementary, not competing. A Swiss in-house legal team at a multinational company could use both:
### - **Anthropic Legal** for English-language vendor contracts, NDA triage from the sales team, daily legal briefings, and Slack-integrated workflow management.
### - **BetterCallClaude** for Swiss-specific employment disputes, FINMA regulatory compliance, nDSG data protection analysis, litigation preparation with BGE research, and court submissions in German, French, or Italian.
### The Legal plugin handles the high-volume commercial workflow; BetterCallClaude handles the jurisdiction-specific legal depth. Together, they cover both breadth and depth.
### ---
### ## Conclusion
### Both plugins are good tools designed for different purposes. The Anthropic Legal plugin excels at streamlining in-house legal operations — contract review, NDA screening, vendor management, and stakeholder communication — with a flexible playbook system and corporate tool integrations. It is the right choice for teams whose work centers on English-language commercial agreements.
### BetterCallClaude is built for a different problem: Swiss legal practice requires jurisdiction-specific knowledge (26 cantons, three official legal languages, distinct procedural codes), live access to Swiss court databases, verified citations that hold up in court, and document formats that meet ZPO requirements. These are not features that can be added through playbook configuration — they require purpose-built agents, MCP servers connected to Swiss legal databases, and deep integration with Swiss legal methodology.
### The right tool depends on the job. For Swiss law, BetterCallClaude is the specialized instrument.
### ### Further Reading
### - [Employment Case Walkthrough](employment-case-walkthrough.md) — Full six-step tutorial with the Keller v. AlphaFin AG case (also available in [DE](arbeitsrecht-fallbeispiel.md), [FR](cas-pratique-droit-du-travail.md), [IT](caso-pratico-diritto-del-lavoro.md))
### - [Installation Guide](../INSTALL.md) — Setup instructions for Claude Code CLI and Cowork Desktop
### - [Command Reference](../command-reference.md) — Full documentation of all 18 BetterCallClaude commands
### ---
### *Professional disclaimer: This comparison is provided for informational purposes. BetterCallClaude is a legal research and analysis tool — all outputs require review and validation by a qualified Swiss lawyer before use. This does not constitute legal advice.*
