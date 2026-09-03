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
    assert.doesNotMatch(byProduct, /api-delpi|API_DELPI/);
    assert.match(abc, /DataTable/);
    assert.match(abc, /runTabularExport/);
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
    const shellOpen = filters.indexOf("<CommercialFilterBarShell");
    const shellClose = filters.indexOf("</CommercialFilterBarShell>");
    const filtersRow = filters.indexOf("<FiltersRow");
    assert.ok(shellOpen >= 0 && shellClose > shellOpen);
    assert.ok(filtersRow > shellOpen && filtersRow < shellClose);
  });
});
