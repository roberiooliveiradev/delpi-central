import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("Portfolio billing tables — estrutural", () => {
  it("painel Faturamento usa filtros compartilhados + tabelas kit", () => {
    const page = readFileSync(join(here, "../pages/CustomersPage.tsx"), "utf8");
    assert.match(page, /PortfolioBillingFiltersBar/);
    assert.match(page, /PortfolioBillingByProductTable/);
    assert.match(page, /PortfolioBillingAbcTable/);
    assert.match(page, /usePortfolioBillingWorkspaceFilters/);
    assert.match(page, /value: "abc"/);
    assert.match(page, /active=\{panel === "abc"\}/);
    assert.match(page, /panel === "billing" \|\| panel === "abc"/);
    assert.match(page, /cm-customers-page__vision/);
    assert.match(page, /workspacePanel/);
    assert.match(page, /panelBilling/);
    assert.match(page, /LineChart/);
    const abcMount = page.indexOf("<PortfolioBillingAbcTable");
    assert.ok(abcMount >= 0);
    const abcSlice = page.slice(abcMount, abcMount + 280);
    assert.match(abcSlice, /active=\{panel === "abc"\}/);
    assert.doesNotMatch(abcSlice, /active=\{panel === "billing"\}/);
  });

  it("tabelas usam CommercialDataTable e export tabular", () => {
    const byProduct = readFileSync(
      join(here, "PortfolioBillingByProductTable.tsx"),
      "utf8",
    );
    const abc = readFileSync(join(here, "PortfolioBillingAbcTable.tsx"), "utf8");
    assert.match(byProduct, /DataTable/);
    assert.match(byProduct, /runTabularExport/);
    assert.match(byProduct, /sentenceHeadersWrap/);
    assert.match(byProduct, /usePortfolioBillingTablePreferences/);
    assert.match(byProduct, /CommercialTableColumnVisibilityMenu/);
    assert.match(byProduct, /enableColumnReorder/);
    assert.doesNotMatch(byProduct, /api-delpi|API_DELPI/);
    assert.match(abc, /DataTable/);
    assert.match(abc, /runTabularExport/);
    assert.match(abc, /OtdCustomerIdentityCell/);
    assert.match(abc, /useCustomerAvatarPresence/);
    assert.doesNotMatch(abc, /<table[\s>]/);
  });

  it("filtros Faturamento/ABC seguem padrão Clientes (chips + FilterBarShell)", () => {
    const filters = readFileSync(
      join(here, "PortfolioBillingFiltersBar.tsx"),
      "utf8",
    );
    assert.match(filters, /CommercialFilterBarShell/);
    assert.match(filters, /CommercialMultiSelectField/);
    assert.match(filters, /CommercialScopeChipBar/);
    assert.match(filters, /BILLING_SERIES_PRESET_OPTIONS/);
    assert.match(filters, /CommercialClearFiltersButton/);
    assert.match(filters, /clearRecorteFilters/);
    assert.doesNotMatch(filters, /FiltersRow/);
    assert.doesNotMatch(filters, /PeriodCompareControls/);
  });

  it("limpar filtros usa ClearFiltersButton do kit", () => {
    const page = readFileSync(join(here, "../pages/CustomersPage.tsx"), "utf8");
    const byProduct = readFileSync(
      join(here, "PortfolioBillingByProductTable.tsx"),
      "utf8",
    );
    const abc = readFileSync(join(here, "PortfolioBillingAbcTable.tsx"), "utf8");
    const filterBar = readFileSync(
      join(here, "../../../components/FilterBar.tsx"),
      "utf8",
    );
    assert.match(page, /CommercialClearFiltersButton/);
    assert.match(byProduct, /CommercialClearFiltersButton/);
    assert.match(abc, /CommercialClearFiltersButton/);
    assert.match(filterBar, /ClearFiltersButton/);
    assert.doesNotMatch(filterBar, /ActionButton variant="ghost" onClick=\{onReset\}/);
    assert.doesNotMatch(filterBar, /RotateCcw/);
  });
});
