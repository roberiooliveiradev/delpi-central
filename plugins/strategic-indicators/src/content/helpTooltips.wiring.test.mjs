#!/usr/bin/env node
/**
 * Garante que toda chave SI_HELP aparece no código admin (/settings).
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const uiRoot = join(root, "ui");

const ADMIN_UI_FILES = [
  "pages/SettingsPage.tsx",
  "components/RefreshSnapshotButton.tsx",
  "components/CatalogAdminWorkspace.tsx",
  "components/AdminDepartmentsWorkspace.tsx",
  "components/CatalogStructureValidationWorkspace.tsx",
  "components/AdminDepartmentFormDrawer.tsx",
  "components/AdminIndicatorFormDrawer.tsx",
  "components/AdminGoalsWorkspace.tsx",
  "components/IndicatorGoalForm.tsx",
  "components/SettingsStructuredEditor.tsx",
  "components/SettingsParametersForm.tsx",
  "components/SettingsGovernanceForm.tsx",
  "components/AdminConfigImportExportPanel.tsx",
  "components/AuditWorkspacePanel.tsx",
  "components/AuditTimelinePanel.tsx",
  "components/SettingsOverviewWorkspace.tsx",
].map((segment) => join(uiRoot, segment));

function readAdminUiSource() {
  return ADMIN_UI_FILES.map((path) => readFileSync(path, "utf8")).join("\n");
}

function helpAccessPath(key) {
  return `SI_HELP.${key.split(".").join(".")}`;
}

describe("SI_HELP wiring admin", () => {
  it("toda chave do catálogo é referenciada na UI de configuração", async () => {
    const { listSiHelpKeys } = await import(
      pathToFileURL(join(root, "content/helpTooltips.ts")).href
    );
    const source = readAdminUiSource();
    const missing = [];

    for (const key of listSiHelpKeys()) {
      const referenced =
        source.includes(helpAccessPath(key)) ||
        source.includes(`getSiHelp("${key}")`);

      if (!referenced) {
        missing.push(key);
      }
    }

    assert.equal(
      missing.length,
      0,
      `Chaves SI_HELP sem referência na UI admin:\n${missing.join("\n")}`,
    );
  });
});
