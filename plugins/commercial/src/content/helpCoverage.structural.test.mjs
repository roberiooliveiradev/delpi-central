#!/usr/bin/env node
/**
 * Gate: gaps de help ⊆ allowlist; allowlist sem entradas mortas.
 */
import assert from "node:assert/strict";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

import {
  collectHelpCoverageGaps,
  gapKey,
  loadAllowlist,
  partitionAgainstAllowlist,
} from "./auditHelpCoverage.mjs";

const contentDir = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(contentDir, "..");
const allowlistPath = join(contentDir, "help_coverage_allowlist.json");

describe("help coverage gate (E1.S3)", () => {
  it("nenhum gap novo fora da allowlist e nenhuma entrada stale", () => {
    const gaps = collectHelpCoverageGaps(srcRoot);
    const allowlist = loadAllowlist(allowlistPath);
    const { unexpected, staleAllowlist } = partitionAgainstAllowlist(gaps, allowlist);

    assert.deepEqual(
      unexpected.map(gapKey),
      [],
      `gaps sem allowlist:\n${unexpected.map(gapKey).join("\n")}`,
    );
    assert.deepEqual(
      staleAllowlist.map(gapKey),
      [],
      `allowlist stale (já cobertos — remova da lista):\n${staleAllowlist.map(gapKey).join("\n")}`,
    );
  });

  it("allowlist só contém kind field|column e ids não vazios", () => {
    const allowlist = loadAllowlist(allowlistPath);
    assert.ok(allowlist.length > 0, "allowlist vazia inesperada na baseline");
    for (const entry of allowlist) {
      assert.ok(entry.file, "file obrigatório");
      assert.ok(entry.kind === "field" || entry.kind === "column", entry.kind);
      assert.ok(String(entry.id).trim(), `id vazio em ${entry.file}`);
    }
  });
});
