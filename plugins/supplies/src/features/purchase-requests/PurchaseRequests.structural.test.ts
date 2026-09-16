import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { mapPurchaseRequestsFetchError } from "./content";
import {
  buildListSearchParams,
  buildRequestKey,
  buildUrlSearch,
  createDefaultQuery,
  parseQueryFromSearch,
  parseRequestKey,
} from "./query";

const dir = dirname(fileURLToPath(import.meta.url));

describe("PurchaseRequests feature", () => {
  it("App liga a página real em vez do placeholder", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/PurchaseRequestsPage/);
    expect(app).not.toMatch(/Lista e detalhe de SC entram na jornada C1/);
  });

  it("cliente fala só com supplies-api", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/suppliesApiUrl\(`\/purchase-requests/);
    expect(api).not.toMatch(/purchase-requests-api/);
    expect(api).not.toMatch(/api-delpi/);
  });

  it("usa PageHero, auto-filtros, refresh e SectionCard", () => {
    const page = readFileSync(join(dir, "PurchaseRequestsPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("PurchaseRequestsFilters");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("SuppliesSectionHintLabel");
    expect(page).toContain("lastUpdatedAt");
    expect(page).toContain("resolveDefaultBranch");
    expect(page).toContain("PurchaseRequestsListTable");
    expect(page).toContain("formatSuppliesUnitLabel");
    expect(page).not.toContain("onApply");
    expect(page).not.toContain("applyFilters");
    expect(page).not.toContain("sp-purchase-requests__hero");
    expect(page).not.toContain("<select");
    expect(page).not.toContain('type="date"');

    const filters = readFileSync(join(dir, "PurchaseRequestsFilters.tsx"), "utf8");
    expect(filters).toContain("SuppliesFilterBarShell");
    expect(filters).toContain("sp-filter-bar__header");
    expect(filters).toContain("C.moreFilters");
    expect(filters).toContain("C.lessFilters");
    expect(filters).toContain("SuppliesClearFiltersButton");
    expect(filters).toContain("hasActivePurchaseRequestsFilters");
    expect(filters).toContain("buildSuppliesUnitOptions");
    expect(filters).toContain("useCommittedTextFilter");
    expect(filters).toContain("SP_HELP.purchaseRequestsFilters");
    expect(filters).not.toContain("Aplicar filtros");
    expect(filters).not.toContain("onApply");
    expect(filters).not.toContain("sp-list-filters__hint");
  });

  it("toolbar canônica com export gated, metadata e link SC", () => {
    const table = readFileSync(join(dir, "PurchaseRequestsListTable.tsx"), "utf8");
    expect(table).toContain("SuppliesDataListToolbar");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("C.tableMeta");
    expect(table).toContain("SuppliesEntityLink");
    expect(table).toContain("SuppliesStatusBadge");
    expect(table).toContain("canExport");
    expect(table).toContain("onExport");
    expect(table).toContain("sp-list-table-region");

    const config = readFileSync(join(dir, "purchaseRequestsTableConfig.ts"), "utf8");
    expect(config).toContain("supplies:purchase-requests:column-prefs:v1");
    expect(config).toContain("supplies:purchase-requests:table-font-size:v1");
    expect(config).not.toContain("purchase-orders");
  });

  it("CSS não recria botão/filtro do kit e usa região de tabela compartilhada", () => {
    const css = readFileSync(join(dir, "../../index.css"), "utf8");
    expect(css).not.toMatch(/sp-purchase-requests__btn\b/);
    expect(css).not.toMatch(/sp-purchase-requests__hero\b/);
    expect(css).toMatch(/sp-list-table-region/);
    expect(css).toMatch(/sp-list-filters/);
  });

  it("query positive + sibling + negative", () => {
    const query = createDefaultQuery("01");
    query.request_number = "100";
    query.overall_stages = ["awaiting_order"];
    const params = buildListSearchParams(query);
    expect(params.get("branch")).toBe("01");
    expect(params.get("request_number")).toBe("100");
    expect(params.getAll("overall_stage")).toEqual(["awaiting_order"]);

    const sibling = parseQueryFromSearch("?branch=02&request=02:200", "01");
    expect(sibling.branch).toBe("02");
    expect(parseRequestKey(sibling.request)).toEqual({
      branch: "02",
      requestNumber: "200",
    });
    expect(buildUrlSearch(sibling)).toContain("branch=02");
    expect(buildUrlSearch(sibling)).toContain("request=02%3A200");

    expect(parseRequestKey("invalid")).toBeNull();
    expect(buildRequestKey("01", "100")).toBe("01:100");
    expect(parseQueryFromSearch("?overall_stage=not-a-stage", "01").overall_stages).toEqual([]);
  });

  it("mapeia 403 positive/sibling e preserva mensagem genérica (negative)", () => {
    expect(mapPurchaseRequestsFetchError("403 Forbidden")).toMatch(/filial/i);
    expect(mapPurchaseRequestsFetchError("Request failed with status 403")).toMatch(/filial/i);
    expect(mapPurchaseRequestsFetchError("timeout upstream")).toBe("timeout upstream");
  });
});
