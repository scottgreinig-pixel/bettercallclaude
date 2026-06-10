# LinkedIn / aiwat.ch Post Draft — BetterCallClaude v4.8.0

> **This file is a draft for external publication. It is NOT part of the plugin and should not be committed to the repo.**

---

**Anthropic ha costruito il plugin legale per il Delaware. Noi per la Svizzera.**

Quando Anthropic ha rilasciato il suo Legal plugin ufficiale per Claude — con contract review, NDA triage e playbook locali — ha validato una categoria. Ma i playbook di default parlano di Delaware, New York e California.

Con BetterCallClaude v4.8.0 portiamo lo stesso pattern alla giurisdizione svizzera:

- **NDA triage svizzero** (GREEN/YELLOW/RED): criteri basati su diritto svizzero, Art. 160 ss. CO, Convenzione di Lugano, diritto imperativo. Non Delaware law.
- **Playbook locale** (`bettercallclaude.local.md`): posizioni contrattuali standard, soglie di rischio, formato citazioni, lingua di output — personalizzato per il vostro studio. Template in DE/FR/IT/EN.
- **Contract review con deviazioni**: ogni clausola confrontata con le posizioni del playbook. Conforme, scostamento accettabile, da negoziare, inaccettabile.
- **Coesistenza**: i due plugin convivono. Per il diritto svizzero fa fede BCC, per il diritto US il plugin Anthropic.
- **9 server MCP** su fonti ufficiali (BGE, Fedlex, entscheidsuche) — non "conoscenza del modello", ma dati verificabili.
- **Privacy**: hook Art. 321 StGB per il segreto professionale, assente nel plugin Anthropic.

Il tono non è competitivo. Anthropic ha costruito le fondamenta; noi copriamo la giurisdizione. Chi lavora con il diritto svizzero ora ha uno strumento dedicato.

Disponibile su GitHub: github.com/fedec65/bettercallclaude

#LegalTech #SwissLaw #AI #Claude #BetterCallClaude
