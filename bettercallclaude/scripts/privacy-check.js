#!/usr/bin/env node
// BetterCallClaude Privacy Check Hook
// Node.js port of privacy-check.sh — cross-platform (Windows/macOS/Linux)
// Scans tool input for Anwaltsgeheimnis (attorney-client privilege) patterns
// per Art. 321 StGB and Art. 13 BGFA across DE/FR/IT
//
// Reads tool input JSON from stdin, checks for privileged content patterns.
// Writes hookSpecificOutput JSON to stdout when a match is found.
// Exits silently (exit 0) to allow when no match.

process.stdin.setEncoding('utf8');

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  let data;
  try {
    data = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  // Extract content fields from tool input
  const parts = [];
  if (data.content)    parts.push(data.content);     // Write tool
  if (data.new_string) parts.push(data.new_string);  // Edit tool
  if (data.command)    parts.push(data.command);      // Bash tool
  const content = parts.join(' ');

  if (!content) process.exit(0);

  // Anwaltsgeheimnis patterns across DE/FR/IT (case-insensitive)
  // Mirrors the patterns in privacy-check.sh exactly
  const patterns = [
    /anwalt.*geheimnis/i,
    /mandatsgeheimnis/i,
    /berufsgeheimnis/i,
    /gesch\u00e4ftsgeheimnis/i,
    /vertraulich/i,
    /streng\s+vertraulich/i,
    /secret\s+professionnel/i,
    /confidentiel/i,
    /strictement\s+confidentiel/i,
    /segreto\s+professionale/i,
    /riservato/i,
    /strettamente\s+riservato/i,
    /Art\.\s*321\s*StGB/i,
    /Art\.\s*13\s*BGFA/i,
  ];

  for (const pattern of patterns) {
    if (pattern.test(content)) {
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'ask',
          permissionDecisionReason:
            `Potential attorney-client privileged content detected (Anwaltsgeheimnis, Art. 321 StGB). Pattern matched: ${pattern.source}. Please confirm this content should be written/sent.`
        }
      }));
      process.exit(0);
    }
  }

  // No privileged content detected — silent exit allows the operation
  process.exit(0);
});
