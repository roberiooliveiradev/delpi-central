#!/usr/bin/env node
/**
 * CLI: audit Commercial help coverage (fields + table columns).
 * Usage:
 *   node scripts/audit_help_coverage.mjs
 *   node scripts/audit_help_coverage.mjs --write-allowlist
 *   node scripts/audit_help_coverage.mjs --markdown
 */
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  collectHelpCoverageGaps,
  formatGapsMarkdown,
  gapKey,
  loadAllowlist,
  partitionAgainstAllowlist,
} from "../src/content/auditHelpCoverage.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const pluginRoot = join(here, "..");
const srcRoot = join(pluginRoot, "src");
const allowlistPath = join(srcRoot, "content/help_coverage_allowlist.json");

const args = new Set(process.argv.slice(2));
const gaps = collectHelpCoverageGaps(srcRoot);

if (args.has("--write-allowlist")) {
  const payload = {
    generatedAt: new Date().toISOString().slice(0, 10),
    note: "Baseline gaps; waves must only remove entries. Do not grow without PR justification.",
    gaps: gaps.map((g) => ({ file: g.file, kind: g.kind, id: g.id })),
  };
  writeFileSync(allowlistPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  console.log(`Wrote ${gaps.length} gaps → ${allowlistPath}`);
  process.exit(0);
}

let allowlist = [];
try {
  allowlist = loadAllowlist(allowlistPath);
} catch {
  console.warn("No allowlist yet — treating all gaps as unexpected.");
}

const { unexpected, allowlisted, staleAllowlist } = partitionAgainstAllowlist(
  gaps,
  allowlist,
);

console.log(`Help coverage gaps: ${gaps.length} total`);
console.log(`  allowlisted: ${allowlisted.length}`);
console.log(`  unexpected:  ${unexpected.length}`);
console.log(`  stale allowlist: ${staleAllowlist.length}`);

if (args.has("--markdown") || unexpected.length || gaps.length) {
  console.log("\n## Gaps\n");
  console.log(formatGapsMarkdown(gaps));
}

if (unexpected.length) {
  console.error("\nUnexpected gaps (not in allowlist):");
  for (const g of unexpected) console.error(`  ${gapKey(g)}`);
  process.exit(1);
}

if (staleAllowlist.length) {
  console.error("\nStale allowlist entries (no longer gaps):");
  for (const g of staleAllowlist) console.error(`  ${gapKey(g)}`);
  process.exit(1);
}

process.exit(0);
