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

  it("filtros usam FilterBarShell e multi-select do kit", () => {
    const filters = readFileSync(
      join(here, "PortfolioBillingFiltersBar.tsx"),
      "utf8",
    );
    assert.match(filters, /CommercialFilterBarShell/);
    assert.match(filters, /CommercialMultiSelectField/);
    assert.match(filters, /FiltersRow/);
    assert.match(filters, /variant="bare"/);
    assert.match(filters, /size="sm"/);
    const shellOpen = filters.indexOf("<CommercialFilterBarShell");
    const shellClose = filters.indexOf("</CommercialFilterBarShell>");
    const filtersRow = filters.indexOf("<FiltersRow");
    assert.ok(shellOpen >= 0 && shellClose > shellOpen);
    assert.ok(filtersRow > shellOpen && filtersRow < shellClose);
  });
});
