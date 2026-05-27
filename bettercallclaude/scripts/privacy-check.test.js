#!/usr/bin/env node
/**
 * Standalone tests for privacy-check.js. Runs with plain `node` — no test
 * framework dependency.
 *
 *   node bettercallclaude/scripts/privacy-check.test.js
 */

'use strict';

const assert = require('node:assert');
const {
  classify,
  classifyWithMode,
  isOllamaTool,
  resolvePrivacyMode,
  extractTextFromInput,
  extractPathHint,
} = require('./privacy-check.js');

let passed = 0;
let failed = 0;

function t(name, fn) {
  try {
    fn();
    console.log('  ok  ' + name);
    passed++;
  } catch (e) {
    console.error('  FAIL ' + name);
    console.error('       ' + (e && e.message ? e.message : e));
    failed++;
  }
}

// -------------------------------------------------------------------------
// classify() — returns {category, strength} or null
// -------------------------------------------------------------------------

console.log('privacy-check: strong patterns');

t('triggers on "Anwaltsgeheimnis"', () => {
  const r = classify('Dies ist Anwaltsgeheimnis.', '');
  assert.strictEqual(r.category, 'anwaltsgeheimnis');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "Mandatsgeheimnis"', () => {
  const r = classify('Unter Mandatsgeheimnis.', '');
  assert.strictEqual(r.category, 'mandatsgeheimnis');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "secret professionnel"', () => {
  const r = classify('Relève du secret professionnel.', '');
  assert.strictEqual(r.category, 'secret-professionnel-fr');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "segreto professionale"', () => {
  const r = classify('Coperto da segreto professionale.', '');
  assert.strictEqual(r.category, 'segreto-professionale-it');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "streng vertraulich"', () => {
  const r = classify('STRENG VERTRAULICH — nicht weitergeben.', '');
  assert.strictEqual(r.category, 'streng-vertraulich');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on Art. 321 StGB', () => {
  const r = classify('Siehe Art. 321 StGB.', '');
  assert.strictEqual(r.category, 'art-321-stgb');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on Art. 13 BGFA', () => {
  const r = classify('Verletzt Art. 13 BGFA.', '');
  assert.strictEqual(r.category, 'art-13-bgfa');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on Art. 47 BankG', () => {
  const r = classify('Siehe Art. 47 BankG.', '');
  assert.strictEqual(r.category, 'art-47-bankg');
  assert.strictEqual(r.strength, 'strong');
});

console.log('privacy-check: new strong patterns (DE)');

t('triggers on "Verschwiegenheitspflicht"', () => {
  const r = classify('Die Verschwiegenheitspflicht gilt.', '');
  assert.strictEqual(r.category, 'verschwiegenheitspflicht');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "Geheimhaltungspflicht"', () => {
  const r = classify('Die Geheimhaltungspflicht besteht.', '');
  assert.strictEqual(r.category, 'geheimhaltungspflicht');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "anwaltliche Verschwiegenheit"', () => {
  const r = classify('Unter anwaltlicher Verschwiegenheit.', '');
  assert.strictEqual(r.category, 'anwaltliche-verschwiegenheit');
  assert.strictEqual(r.strength, 'strong');
});

console.log('privacy-check: new strong patterns (FR)');

t('triggers on "obligation de discrétion"', () => {
  const r = classify('Soumis à obligation de discrétion.', '');
  assert.strictEqual(r.category, 'obligation-discretion-fr');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "secret du mandat"', () => {
  const r = classify('Protégé par le secret du mandat.', '');
  assert.strictEqual(r.category, 'secret-du-mandat-fr');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "confidentialité du mandat"', () => {
  const r = classify('La confidentialité du mandat exige...', '');
  assert.strictEqual(r.category, 'confidentialite-du-mandat-fr');
  assert.strictEqual(r.strength, 'strong');
});

console.log('privacy-check: new strong patterns (IT)');

t('triggers on "vincolo professionale"', () => {
  const r = classify('In virtù del vincolo professionale.', '');
  assert.strictEqual(r.category, 'vincolo-professionale-it');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "obbligo di riservatezza"', () => {
  const r = classify('Obbligo di riservatezza sussiste.', '');
  assert.strictEqual(r.category, 'obbligo-riservatezza-it');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "segreto d\'ufficio"', () => {
  const r = classify('Coperto da segreto d\'ufficio.', '');
  assert.strictEqual(r.category, 'segreto-d-ufficio-it');
  assert.strictEqual(r.strength, 'strong');
});

console.log('privacy-check: new strong patterns (EN)');

t('triggers on "attorney-client privilege"', () => {
  const r = classify('This is protected by attorney-client privilege.', '');
  assert.strictEqual(r.category, 'attorney-client-privilege-en');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "legal professional privilege"', () => {
  const r = classify('Covered by legal professional privilege.', '');
  assert.strictEqual(r.category, 'legal-professional-privilege-en');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "solicitor-client privilege"', () => {
  const r = classify('Under solicitor-client privilege.', '');
  assert.strictEqual(r.category, 'solicitor-client-privilege-en');
  assert.strictEqual(r.strength, 'strong');
});

t('triggers on "privileged and confidential"', () => {
  const r = classify('This communication is privileged and confidential.', '');
  assert.strictEqual(r.category, 'privileged-confidential-en');
  assert.strictEqual(r.strength, 'strong');
});

// -------------------------------------------------------------------------
// classify() — weak patterns
// -------------------------------------------------------------------------

console.log('privacy-check: weak patterns (no discriminator)');

t('does NOT trigger on bare "vertraulich" without context', () => {
  assert.strictEqual(classify('Diese Information ist vertraulich.', '/tmp/notes.md'), null);
});

t('does NOT trigger on bare "confidentiel" without context', () => {
  assert.strictEqual(classify('Message confidentiel.', '/tmp/x.md'), null);
});

t('does NOT trigger on bare "riservato" without context', () => {
  assert.strictEqual(classify('Documento riservato.', '/tmp/x.md'), null);
});

t('does NOT trigger on bare "confidential" without context', () => {
  assert.strictEqual(classify('Confidential memo.', '/tmp/notes.md'), null);
});

console.log('privacy-check: weak patterns + path discriminator');

t('triggers on "vertraulich" when path contains /klient/', () => {
  const r = classify('Notiz: vertraulich.', '/home/u/klient/acme/notes.md');
  assert.strictEqual(r.category, 'vertraulich-bare+context');
  assert.strictEqual(r.strength, 'weak');
});

t('triggers on "confidential" when path contains /case/', () => {
  const r = classify('Confidential memo.', '/home/u/cases/2024-smith/memo.md');
  assert.strictEqual(r.category, 'confidential-bare+context');
  assert.strictEqual(r.strength, 'weak');
});

t('triggers on "riservato" when path contains /dossier/', () => {
  const r = classify('Riservato.', '/Users/u/dossiers/rossi/nota.md');
  assert.strictEqual(r.category, 'riservato-bare+context');
  assert.strictEqual(r.strength, 'weak');
});

t('triggers on "confidentiel" when path contains /mandant/', () => {
  // "strictement confidentiel" is a STRONG pattern, so this hits strong first.
  const r = classify('Strictement confidentiel.', '/home/u/mandants/muller/lettre.md');
  assert.strictEqual(r.category, 'strictement-confidentiel-fr');
  assert.strictEqual(r.strength, 'strong');
});

console.log('privacy-check: weak patterns + content discriminator');

t('triggers on "vertraulich" when content mentions "Mandant"', () => {
  const r = classify('Notiz zum Mandanten Meier: vertraulich.', '/tmp/notes.md');
  assert.strictEqual(r.category, 'vertraulich-bare+context');
  assert.strictEqual(r.strength, 'weak');
});

t('triggers on two co-occurring weak markers', () => {
  const r = classify('Confidential and vertraulich.', '/tmp/x.md');
  assert.strictEqual(r.category, 'vertraulich-bare+context');
  assert.strictEqual(r.strength, 'weak');
});

// -------------------------------------------------------------------------
// classifyWithMode() — mode-aware decision logic
// -------------------------------------------------------------------------

console.log('privacy-check: classifyWithMode — balanced (default)');

t('balanced: strong pattern → ask', () => {
  const r = classifyWithMode('Anwaltsgeheimnis here.', '', 'balanced', 'Write');
  assert.strictEqual(r.decision, 'ask');
  assert.strictEqual(r.category, 'anwaltsgeheimnis');
});

t('balanced: weak pattern + context → ask', () => {
  const r = classifyWithMode('Vertraulich info.', '/home/u/klient/acme/n.md', 'balanced', 'Write');
  assert.strictEqual(r.decision, 'ask');
  assert.strictEqual(r.category, 'vertraulich-bare+context');
});

t('balanced: weak pattern without context → null (allow)', () => {
  const r = classifyWithMode('Vertraulich info.', '/tmp/x.md', 'balanced', 'Write');
  assert.strictEqual(r, null);
});

t('balanced: no pattern → null (allow)', () => {
  const r = classifyWithMode('Hello world.', '', 'balanced', 'Write');
  assert.strictEqual(r, null);
});

console.log('privacy-check: classifyWithMode — strict');

t('strict: strong pattern → deny', () => {
  const r = classifyWithMode('Anwaltsgeheimnis.', '', 'strict', 'Write');
  assert.strictEqual(r.decision, 'deny');
});

t('strict: no pattern → deny (strict blocks all non-Ollama)', () => {
  const r = classifyWithMode('Hello world, no pattern.', '/tmp/x.md', 'strict', 'Write');
  assert.strictEqual(r.decision, 'deny');
  assert.strictEqual(r.category, 'strict-mode-block');
});

t('strict: Ollama tool → null (exempt, local processing)', () => {
  const r = classifyWithMode('Anwaltsgeheimnis.', '', 'strict', 'mcp__ollama__translate');
  assert.strictEqual(r, null);
});

t('strict: non-Ollama MCP tool → deny', () => {
  const r = classifyWithMode('Neutral text.', '', 'strict', 'mcp__entscheidsuche__search');
  assert.strictEqual(r.decision, 'deny');
});

t('strict: Bash tool → deny', () => {
  const r = classifyWithMode('Neutral text.', '', 'strict', 'Bash');
  assert.strictEqual(r.decision, 'deny');
});

t('strict: empty content non-Ollama MCP → deny (no bypass)', () => {
  // Regression: MCP calls with only numeric params must still be blocked in strict mode.
  const r = classifyWithMode('', '', 'strict', 'mcp__entscheidsuche__search');
  assert.strictEqual(r.decision, 'deny');
  assert.strictEqual(r.category, 'strict-mode-block');
});

t('strict: empty content Ollama → null (exempt)', () => {
  const r = classifyWithMode('', '', 'strict', 'mcp__ollama__translate');
  assert.strictEqual(r, null);
});

console.log('privacy-check: classifyWithMode — cloud');

t('cloud: strong pattern → ask', () => {
  const r = classifyWithMode('Anwaltsgeheimnis.', '', 'cloud', 'Write');
  assert.strictEqual(r.decision, 'ask');
  assert.strictEqual(r.category, 'anwaltsgeheimnis');
});

t('cloud: weak pattern + context → null (allow without prompt)', () => {
  const r = classifyWithMode('Vertraulich info.', '/home/u/klient/acme/n.md', 'cloud', 'Write');
  assert.strictEqual(r, null);
});

t('cloud: no pattern → null (allow)', () => {
  const r = classifyWithMode('Hello world.', '', 'cloud', 'Write');
  assert.strictEqual(r, null);
});

console.log('privacy-check: isOllamaTool');

t('identifies mcp__ollama__translate as Ollama', () => {
  assert.strictEqual(isOllamaTool('mcp__ollama__translate'), true);
});

t('identifies mcp__ollama__summarize as Ollama', () => {
  assert.strictEqual(isOllamaTool('mcp__ollama__summarize'), true);
});

t('rejects mcp__entscheidsuche__search', () => {
  assert.strictEqual(isOllamaTool('mcp__entscheidsuche__search'), false);
});

t('rejects Write', () => {
  assert.strictEqual(isOllamaTool('Write'), false);
});

t('rejects empty string', () => {
  assert.strictEqual(isOllamaTool(''), false);
});

// -------------------------------------------------------------------------
// resolvePrivacyMode()
// -------------------------------------------------------------------------

console.log('privacy-check: resolvePrivacyMode');

t('defaults to balanced when env var is unset', () => {
  delete process.env.CLAUDE_PLUGIN_USER_CONFIG;
  assert.strictEqual(resolvePrivacyMode(), 'balanced');
});

t('reads strict from env var', () => {
  process.env.CLAUDE_PLUGIN_USER_CONFIG = JSON.stringify({ privacy_mode: 'strict' });
  assert.strictEqual(resolvePrivacyMode(), 'strict');
  delete process.env.CLAUDE_PLUGIN_USER_CONFIG;
});

t('reads cloud from env var', () => {
  process.env.CLAUDE_PLUGIN_USER_CONFIG = JSON.stringify({ privacy_mode: 'cloud' });
  assert.strictEqual(resolvePrivacyMode(), 'cloud');
  delete process.env.CLAUDE_PLUGIN_USER_CONFIG;
});

t('falls back to balanced on invalid mode', () => {
  process.env.CLAUDE_PLUGIN_USER_CONFIG = JSON.stringify({ privacy_mode: 'invalid' });
  assert.strictEqual(resolvePrivacyMode(), 'balanced');
  delete process.env.CLAUDE_PLUGIN_USER_CONFIG;
});

t('falls back to balanced on malformed JSON', () => {
  process.env.CLAUDE_PLUGIN_USER_CONFIG = 'not-json';
  assert.strictEqual(resolvePrivacyMode(), 'balanced');
  delete process.env.CLAUDE_PLUGIN_USER_CONFIG;
});

// -------------------------------------------------------------------------
// Extractors
// -------------------------------------------------------------------------

console.log('privacy-check: extractors');

t('extractTextFromInput handles Write', () => {
  const text = extractTextFromInput('Write', { file_path: '/x', content: 'Anwaltsgeheimnis' });
  assert.ok(text.includes('Anwaltsgeheimnis'));
});

t('extractTextFromInput handles MultiEdit edits[]', () => {
  const text = extractTextFromInput('MultiEdit', {
    file_path: '/x',
    edits: [
      { old_string: 'a', new_string: 'Art. 321 StGB' },
      { old_string: 'b', new_string: 'plain' },
    ],
  });
  assert.ok(text.includes('Art. 321 StGB'));
});

t('extractTextFromInput walks MCP tool inputs', () => {
  const text = extractTextFromInput('mcp__entscheidsuche__search', {
    filters: { query: 'Anwaltsgeheimnis Meier' },
  });
  assert.ok(text.includes('Anwaltsgeheimnis'));
});

t('extractTextFromInput handles Bash command', () => {
  const text = extractTextFromInput('Bash', { command: 'echo Anwaltsgeheimnis' });
  assert.ok(text.includes('Anwaltsgeheimnis'));
});

t('extractPathHint returns file_path', () => {
  assert.strictEqual(extractPathHint({ file_path: '/a/b' }), '/a/b');
});

t('extractPathHint returns "" when no path', () => {
  assert.strictEqual(extractPathHint({ content: 'x' }), '');
});

// -------------------------------------------------------------------------
// False-positive guards
// -------------------------------------------------------------------------

console.log('privacy-check: false-positive guards');

t('routine footer is NOT flagged', () => {
  const content =
    'Dear colleague,\n\nThe attached report is confidential and intended only ' +
    'for the addressee. Please delete if received in error.';
  assert.strictEqual(classify(content, '/home/u/reports/2024-q1.md'), null);
});

t('standard README with "confidential" term is NOT flagged', () => {
  const content = 'This repository is public. Do not include confidential data.';
  assert.strictEqual(classify(content, '/home/u/repo/README.md'), null);
});

console.log('');
console.log(passed + ' passed, ' + failed + ' failed');
process.exit(failed === 0 ? 0 : 1);
