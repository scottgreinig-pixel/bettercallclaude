#!/usr/bin/env node
/**
 * BetterCallClaude Privacy Check Hook
 *
 * PreToolUse hook that detects potential attorney-client privileged content
 * (Anwaltsgeheimnis / Art. 321 StGB, Art. 13 BGFA) across DE/FR/IT/EN before
 * it leaves the machine via Write, Edit, MultiEdit, Bash, WebFetch, or any
 * MCP tool.
 *
 * Strategy:
 *   - Strong patterns (attorney-specific terms, legal article references)
 *     return "ask" — the user is prompted and can choose to proceed.
 *   - Weak patterns (bare "confidential", "vertraulich", "confidentiel",
 *     "riservato") return "ask" when a discriminator is present (legal-context
 *     file path or another privilege marker), so routine document footers
 *     do not flood the user with permission prompts.
 *
 * Privacy modes (read from CLAUDE_PLUGIN_USER_CONFIG or default "balanced"):
 *   - strict:   All non-Ollama tool calls → deny. Ollama (local) is exempt.
 *   - balanced:  Strong → ask, weak+context → ask. Default.
 *   - cloud:     Strong → ask, weak → allow (no prompt).
 *
 * Per Anthropic hooks spec, stdin is:
 *   {
 *     session_id, cwd, hook_event_name: "PreToolUse",
 *     tool_name: "Write" | "Edit" | "MultiEdit" | "Bash" | "WebFetch" | "mcp__<server>__<tool>" | ...,
 *     tool_input: { ... }
 *   }
 *
 * A legacy flat shape (tool input fields at the top level) is also accepted
 * as a safety net.
 *
 * Output:
 *   - stdout JSON {hookSpecificOutput:{permissionDecision:"deny"|"ask", ...}}
 *     written when privileged content is detected or strict mode blocks.
 *   - Exit code 0 in all non-error paths.
 */

'use strict';

// ---------------------------------------------------------------------------
// Entry point — reads stdin, classifies content, writes hookSpecificOutput.
// ---------------------------------------------------------------------------

function main() {
  process.stdin.setEncoding('utf8');
  let input = '';
  process.stdin.on('data', (chunk) => { input += chunk; });
  process.stdin.on('end', () => {
    let data;
    try { data = JSON.parse(input); } catch { process.exit(0); }

    const toolName = typeof data.tool_name === 'string' ? data.tool_name : '';
    // Accept both the canonical {tool_input: {...}} shape and a legacy flat shape.
    const toolInput = (data.tool_input && typeof data.tool_input === 'object')
      ? data.tool_input
      : data;

    const content = extractTextFromInput(toolName, toolInput);
    const pathHint = extractPathHint(toolInput);
    const mode = resolvePrivacyMode();

    if (!content.trim()) {
      // In strict mode, block all non-Ollama calls even with empty content.
      if (mode === 'strict' && !isOllamaTool(toolName)) {
        const reason =
          'Strict privacy mode: all non-local tool calls are blocked. ' +
          'Swiss law: Art. 321 StGB / Art. 13 BGFA. ' +
          'This content has been blocked from leaving the machine.';
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'deny',
            permissionDecisionReason: reason,
          },
        }));
      }
      process.exit(0);
    }

    const result = classifyWithMode(content, pathHint, mode, toolName);
    if (!result) { process.exit(0); }

    const reason =
      `Possible attorney-client privileged content detected (category: ${result.category}). ` +
      'Swiss law: Art. 321 StGB / Art. 13 BGFA. ' +
      (result.decision === 'deny'
        ? 'This content has been blocked from leaving the machine.'
        : 'Confirm this content is cleared to leave the machine.');

    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: result.decision,
        permissionDecisionReason: reason,
      },
    }));
    process.exit(0);
  });
}

// ---------------------------------------------------------------------------
// Content extraction
// ---------------------------------------------------------------------------

/** Collect every string in the tool input relevant to content egress. */
function extractTextFromInput(toolName, input) {
  const parts = [];

  // Canonical scalar fields across built-in tools
  const scalarFields = [
    'content',      // Write
    'new_string',   // Edit
    'old_string',   // Edit (for context gating)
    'prompt',       // WebFetch, Task
    'query',        // WebSearch, many MCP search tools
    'url',          // WebFetch
    'command',      // Bash (only scanned when matcher includes Bash)
  ];
  for (const k of scalarFields) {
    if (typeof input[k] === 'string') parts.push(input[k]);
  }

  // MultiEdit: tool_input.edits[].{new_string,old_string}
  if (Array.isArray(input.edits)) {
    for (const e of input.edits) {
      if (e && typeof e === 'object') {
        if (typeof e.new_string === 'string') parts.push(e.new_string);
        if (typeof e.old_string === 'string') parts.push(e.old_string);
      }
    }
  }

  // MCP tools: input shape is arbitrary. Walk every string leaf.
  if (toolName.startsWith('mcp__')) {
    walkStrings(input, (s) => parts.push(s));
  }

  return parts.join('\n');
}

/** Extract a filesystem path hint from the tool input, if present. */
function extractPathHint(input) {
  const candidates = ['file_path', 'path', 'target_file', 'target', 'notebook_path'];
  for (const k of candidates) {
    if (typeof input[k] === 'string') return input[k];
  }
  return '';
}

function walkStrings(node, emit, depth) {
  if (depth === undefined) depth = 0;
  if (depth > 6) return; // hard cap to avoid pathological MCP payloads
  if (typeof node === 'string') { emit(node); return; }
  if (Array.isArray(node)) {
    for (const n of node) walkStrings(n, emit, depth + 1);
    return;
  }
  if (node && typeof node === 'object') {
    for (const v of Object.values(node)) walkStrings(v, emit, depth + 1);
  }
}

// ---------------------------------------------------------------------------
// Privacy mode resolution
// ---------------------------------------------------------------------------

/** Read privacy_mode from CLAUDE_PLUGIN_USER_CONFIG env var (JSON). Default: balanced. */
function resolvePrivacyMode() {
  const raw = process.env.CLAUDE_PLUGIN_USER_CONFIG;
  if (raw) {
    try {
      const cfg = JSON.parse(raw);
      const m = (cfg.privacy_mode || '').toLowerCase().trim();
      if (m === 'strict' || m === 'balanced' || m === 'cloud') return m;
    } catch { /* ignore malformed config */ }
  }
  return 'balanced';
}

// ---------------------------------------------------------------------------
// Pattern classification
// ---------------------------------------------------------------------------

// Strong: high-precision privilege markers. Word-boundary-anchored.
// In balanced/cloud modes these return "ask" (user prompted).
const STRONG_PATTERNS = [
  // German — attorney-specific
  { rx: /\banwalts?\s*geheimnis(s?e)?\b/i,                cat: 'anwaltsgeheimnis' },
  { rx: /\bmandats\s*geheimnis(s?e)?\b/i,                 cat: 'mandatsgeheimnis' },
  { rx: /\bberufs\s*geheimnis(s?e)?\b/i,                  cat: 'berufsgeheimnis' },
  { rx: /\bgesch(ä|ae)fts\s*geheimnis(s?e)?\b/i,          cat: 'geschaeftsgeheimnis' },
  { rx: /\bstreng(\s+|-)?vertraulich\b/i,                 cat: 'streng-vertraulich' },
  { rx: /\bverschwiegenheitspflicht\b/i,                   cat: 'verschwiegenheitspflicht' },
  { rx: /\bgeheimhaltungspflicht\b/i,                      cat: 'geheimhaltungspflicht' },
  { rx: /\banwaltliche(r|s|n)?\s+verschwiegenheit\b/i,     cat: 'anwaltliche-verschwiegenheit' },

  // French
  { rx: /\bsecret\s+professionnel\b/i,                    cat: 'secret-professionnel-fr' },
  { rx: /\bsecret\s+d[' ]affaires?\b/i,                   cat: 'secret-d-affaires-fr' },
  { rx: /\bstrictement\s+confidentiel(le)?\b/i,           cat: 'strictement-confidentiel-fr' },
  { rx: /\bobligation\s+de\s+discr(é|e)tion\b/i,          cat: 'obligation-discretion-fr' },
  { rx: /\bsecret\s+du\s+mandat\b/i,                      cat: 'secret-du-mandat-fr' },
  { rx: /\bconfidentialit(é|e)\s+du\s+mandat\b/i,         cat: 'confidentialite-du-mandat-fr' },

  // Italian
  { rx: /\bsegreto\s+professionale\b/i,                   cat: 'segreto-professionale-it' },
  { rx: /\bsegreto\s+commerciale\b/i,                     cat: 'segreto-commerciale-it' },
  { rx: /\bsegreto\s+del\s+mandato\b/i,                   cat: 'segreto-del-mandato-it' },
  { rx: /\bstrettamente\s+riservato\b/i,                  cat: 'strettamente-riservato-it' },
  { rx: /\bvincolo\s+professionale\b/i,                   cat: 'vincolo-professionale-it' },
  { rx: /\bobbligo\s+di\s+riservatezza\b/i,               cat: 'obbligo-riservatezza-it' },
  { rx: /\bsegreto\s+d[' ]ufficio\b/i,                    cat: 'segreto-d-ufficio-it' },

  // English — privilege terms
  { rx: /\battorney[- ]client\s+privilege\b/i,             cat: 'attorney-client-privilege-en' },
  { rx: /\blegal\s+professional\s+privilege\b/i,           cat: 'legal-professional-privilege-en' },
  { rx: /\bsolicitor[- ]client\s+privilege\b/i,            cat: 'solicitor-client-privilege-en' },
  { rx: /\bprivileged\s+(and\s+)?confidential\b/i,         cat: 'privileged-confidential-en' },

  // Legal article references — language-agnostic
  { rx: /\bArt\.?\s*321\s*(StGB|CP|CPS)\b/i,              cat: 'art-321-stgb' },
  { rx: /\bArt\.?\s*13\s*BGFA\b/i,                        cat: 'art-13-bgfa' },
  { rx: /\bArt\.?\s*162\s*(StGB|CP|CPS)\b/i,              cat: 'art-162-stgb' },
  { rx: /\bArt\.?\s*47\s*BankG\b/i,                       cat: 'art-47-bankg' },
  { rx: /\bArt\.?\s*35\s*FINMAG\b/i,                      cat: 'art-35-finmag' },
  { rx: /\bArt\.?\s*622\s*(CP|StGB|CPS)\b/i,              cat: 'art-622-cp' },
];

// Weak: low-precision terms. Trigger only with a discriminator present.
const WEAK_PATTERNS = [
  { rx: /\bvertraulich\b/i,        cat: 'vertraulich-bare' },
  { rx: /\bconfidentiel(le)?\b/i,  cat: 'confidentiel-bare' },
  { rx: /\briservato\b/i,          cat: 'riservato-bare' },
  { rx: /\bconfidential\b/i,       cat: 'confidential-bare' },
];

// Legal-context path segments that raise a weak match to actionable.
const DISCRIMINATOR_PATH = new RegExp(
  '(^|[\\\\/])' +
  '(klient(en)?|mandant(en)?|client|clients|case|cases|dossier|dossiers' +
  '|fall|faelle|f(ä|ae)lle|akten?|privileged|matter|matters|case[-_]files)' +
  '([\\\\/.]|$)',
  'i'
);

// Legal-context content markers (client/case references, process terms).
const DISCRIMINATOR_CONTENT = new RegExp(
  '\\b(' +
  'mandant(in|en)?|mandataire|mandante|mandatario' +
  '|klient(in|en)?|cliente|client' +
  '|dossier|aktenzeichen|case\\s+number|numero\\s+di\\s+pratica|référence' +
  '|prozess|procès|procedura|procedimento' +
  ')\\b',
  'i'
);

/**
 * Classify content and return {category, strength} or null.
 * strength: 'strong' or 'weak' — used by callers to pick deny vs ask.
 */
function classify(content, pathHint) {
  for (const p of STRONG_PATTERNS) {
    if (p.rx.test(content)) return { category: p.cat, strength: 'strong' };
  }
  for (const p of WEAK_PATTERNS) {
    if (p.rx.test(content) && hasDiscriminator(content, pathHint)) {
      return { category: p.cat + '+context', strength: 'weak' };
    }
  }
  return null;
}

/** Check if a tool name refers to the local Ollama MCP server. */
function isOllamaTool(toolName) {
  return typeof toolName === 'string' && toolName.startsWith('mcp__ollama__');
}

/**
 * Apply privacy mode logic on top of classify().
 * Returns {category, decision} or null.
 *
 * @param {string} toolName — tool being invoked (used for Ollama exemption)
 */
function classifyWithMode(content, pathHint, mode, toolName) {
  if (mode === 'strict') {
    // Ollama is local — always exempt from strict blocking.
    if (isOllamaTool(toolName)) return null;
    // In strict mode, all other content is denied.
    const result = classify(content, pathHint);
    if (result) return { category: result.category, decision: 'deny' };
    return { category: 'strict-mode-block', decision: 'deny' };
  }

  const result = classify(content, pathHint);
  if (!result) return null;

  if (result.strength === 'strong') {
    // Strong patterns prompt the user — they can choose to proceed.
    return { category: result.category, decision: 'ask' };
  }

  // Weak patterns:
  if (mode === 'cloud') {
    // In cloud mode, weak patterns are allowed without prompt.
    return null;
  }

  // balanced (default): weak patterns prompt for confirmation.
  return { category: result.category, decision: 'ask' };
}

function hasDiscriminator(content, pathHint) {
  if (pathHint && DISCRIMINATOR_PATH.test(pathHint)) return true;
  if (DISCRIMINATOR_CONTENT.test(content)) return true;
  // Two distinct weak markers co-occurring is itself suspicious.
  let weakHits = 0;
  for (const p of WEAK_PATTERNS) if (p.rx.test(content)) weakHits++;
  return weakHits >= 2;
}

// ---------------------------------------------------------------------------
// Module export for tests; run as script when invoked directly.
// ---------------------------------------------------------------------------

module.exports = {
  classify,
  classifyWithMode,
  isOllamaTool,
  resolvePrivacyMode,
  extractTextFromInput,
  extractPathHint,
  hasDiscriminator,
  STRONG_PATTERNS,
  WEAK_PATTERNS,
};

if (require.main === module) {
  main();
}
