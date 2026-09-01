#!/usr/bin/env node
/**
 * Matriz mínima SI_HELP — admin /settings.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { describe, it } from "node:test";

const contentDir = dirname(fileURLToPath(import.meta.url));
const helpModuleUrl = pathToFileURL(join(contentDir, "helpTooltips.ts")).href;

function assertHelpKey(source, dottedKey) {
  const parts = dottedKey.split(".");
  assert.ok(parts.length >= 2, `chave dotted inválida: ${dottedKey}`);
  const [section, ...rest] = parts;
  const sectionRe = new RegExp(`\\b${section}\\s*:\\s*\\{`);
  assert.match(source, sectionRe, `seção ${section}`);
  const leaf = rest[rest.length - 1];
  const sectionStart = source.search(sectionRe);
  const after = source.slice(sectionStart);
  const nextSection = after.search(/\n  [a-zA-Z][a-zA-Z0-9]*:\s*\{/);
  const block =
    nextSection > 0 ? after.slice(0, nextSection) : after.slice(0, after.indexOf("\n} as const"));
  assert.match(block, new RegExp(`\\b${leaf}\\s*:`), `faltando ${dottedKey}`);
  assert.match(
    block,
    new RegExp(`${leaf}\\s*:\\s*"[^"]{12,}"`),
    `${dottedKey} string curta ou ausente`,
  );
}

describe("SI_HELP matriz admin", () => {
  const helpSource = readFileSync(join(contentDir, "helpTooltips.ts"), "utf8");

  const requiredKeys = [
    "shell.pageTitle",
    "shell.refreshSnapshots",
    "nav.overview",
    "nav.catalog",
    "nav.goals",
    "nav.system",
    "nav.tabStructure",
    "nav.tabValidation",
    "overview.kpiDepartments",
    "overview.kpiValidationIssues",
    "catalog.validationYear",
    "catalog.validationOnlyIssues",
    "catalog.newIndicator",
    "department.aggregationMode",
    "department.weightPct",
    "indicator.branchValueAggregation",
    "indicator.scopeType",
    "indicator.sourceKey",
    "goals.newYear",
    "goals.duplicateYear",
    "goalForm.goalScopeBranch",
    "goalForm.goalMode",
    "system.importModeReplace",
    "system.importModeMerge",
    "system.auditTimeline",
    "badges.goalScopeConsolidated",
    "badges.severityError",
    "badges.branchAggregationSum",
    "badges.branchAggregationSource",
  ];

  it("exporta chaves obrigatórias documentadas em HELP-CONTENT-ADMIN.md", () => {
    for (const key of requiredKeys) {
      assertHelpKey(helpSource, key);
    }
  });

  it("getSiHelp resolve chaves indexadas em runtime", async () => {
    const { getSiHelp, listSiHelpKeys } = await import(helpModuleUrl);
    const keys = listSiHelpKeys();
    assert.ok(keys.length >= 90, `esperado >= 90 chaves, got ${keys.length}`);
    for (const key of keys) {
      assert.ok(getSiHelp(key).length > 10, key);
    }
    assert.equal(getSiHelp("missing.key"), "");
  });
});
