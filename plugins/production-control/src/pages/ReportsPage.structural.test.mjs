import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("Reports workspace", () => {
  it("registra Relatórios no App, rail e API do MFE", () => {
    const app = readFileSync(join(root, "App.tsx"), "utf8");
    const rail = readFileSync(join(root, "components/PpcRail.tsx"), "utf8");
    const api = readFileSync(join(root, "api/ppcApi.ts"), "utf8");
    const page = readFileSync(join(root, "pages/ReportsPage.tsx"), "utf8");
    const panel = readFileSync(join(root, "components/StockBalancesReportPanel.tsx"), "utf8");
    assert.match(app, /"reports"/);
    assert.match(app, /ReportsPage/);
    assert.match(app, /reportId=\{route\.reportId\}/);
    assert.match(rail, /file-spreadsheet/);
    assert.match(api, /\/reports\/stock-balances/);
    assert.match(page, /ppc-reports-back/);
    assert.match(page, /backToCatalog|Voltar ao catálogo|reports\.backLabel/);
    assert.match(page, /NavigationCard/);
    assert.match(page, /ppc-reports-catalog/);
    assert.match(page, /StockBalancesReportPanel/);
    assert.match(panel, /stockBalances/);
    assert.match(panel, /excelExport/);
    assert.match(panel, /downloadStockBalancesExcel/);
  });
});
