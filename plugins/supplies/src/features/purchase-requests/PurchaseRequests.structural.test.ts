import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { mapPurchaseRequestsFetchError } from "./content";
import {
  authorizeQueryBranches,
  buildListSearchParams,
  buildRequestKey,
  buildUrlSearch,
  createDefaultQuery,
  parseQueryFromSearch,
  parseRequestKey,
} from "./query";

const dir = dirname(fileURLToPath(import.meta.url));

describe("PurchaseRequests feature", () => {
  it("App liga lista e ficha real em vez do placeholder", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/PurchaseRequestsPage/);
    expect(app).toMatch(/PurchaseRequestDetailPage/);
    expect(app).not.toMatch(/Lista e detalhe de SC entram na jornada C1/);
  });

  it("cliente fala só com supplies-api", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/suppliesApiUrl\(`\/purchase-requests/);
    expect(api).not.toMatch(/purchase-requests-api/);
    expect(api).not.toMatch(/api-delpi/);
  });

  it("lista sem painel inline e com redirect legado", () => {
    const page = readFileSync(join(dir, "PurchaseRequestsPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("PurchaseRequestsFilters");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("lastUpdatedAt");
    expect(page).toContain("PurchaseRequestsListTable");
    expect(page).toContain("buildPurchaseRequestDetailPath");
    expect(page).toContain("navigatePluginPath");
    expect(page).toContain("parseRequestKey");
    expect(page).toContain("authorizeQueryBranches");
    expect(page).toContain("canonicalizeUiBranches");
    expect(page).not.toContain("getPurchaseRequest");
    expect(page).not.toContain("detailOpen");
    expect(page).not.toContain("detailLoading");
    expect(page).not.toContain("resolveDefaultBranch");
    expect(page).not.toContain("onApply");
    expect(page).not.toContain("applyFilters");

    const detail = readFileSync(join(dir, "PurchaseRequestDetailPage.tsx"), "utf8");
    expect(detail).toContain("getPurchaseRequest");
    expect(detail).toContain("SuppliesPagePath");
    expect(detail).toContain("SP_HELP.purchaseRequestDetail");
    expect(detail).toContain("SuppliesPersonIdentity");
    expect(detail).toContain("classifyPurchaseRequestDetailError");
  });

  it("filtros Unidade alinhados à Visão geral", () => {
    const filters = readFileSync(join(dir, "PurchaseRequestsFilters.tsx"), "utf8");
    expect(filters).toContain("SuppliesFilterBarShell");
    expect(filters).toContain("SuppliesMultiSelectField");
    expect(filters).toContain("SUPPLIES_UNIT_FILTER_LABEL");
    expect(filters).toContain("canonicalizeUiBranches");
    expect(filters).toContain("emptyLabel=\"Todas\"");
    expect(filters).toContain("searchable");
    expect(filters).toContain("SuppliesSegmentToggle");
    expect(filters).toContain("PERIOD_PRESET_OPTIONS");
    expect(filters).toContain("matchPeriodPreset");
    expect(filters).toContain("C.periodLabel");
    expect(filters).toContain("sp-filter-bar__period-block");
    expect(filters).not.toContain("C.moreFilters");
    expect(filters).not.toContain("showMore");
    expect(filters).not.toContain("searchable={unitOptions.length > 4}");
    expect(filters).not.toContain("Aplicar filtros");
  });

  it("toolbar canônica com href canônico de SC sem is-selected", () => {
    const table = readFileSync(join(dir, "PurchaseRequestsListTable.tsx"), "utf8");
    expect(table).toContain("SuppliesDataListToolbar");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("SuppliesDataCardsSortBar");
    expect(table).toContain("C.tableMeta");
    expect(table).toContain("C.cardsMeta");
    expect(table).toContain("!showCards");
    expect(table).toContain("SuppliesTableFontSizeControls");
    expect(table).toContain("SuppliesTableColumnVisibilityMenu");
    expect(table).toContain("ExcelExportButton");
    expect(table).toContain("SuppliesCompactPagination");
    expect(table).toContain("SuppliesEntityLink");
    expect(table).toContain("SuppliesPersonIdentity");
    expect(table).toContain("buildPurchaseRequestDetailPath");
    expect(table).toContain("PurchaseRequestsCards");
    expect(table).toContain("nextServerSort");
    expect(table).toContain("PURCHASE_REQUESTS_SORTABLE_COLUMNS");
    expect(table).not.toContain("is-selected");
    expect(table).not.toContain("buildRequestKey");
    expect(table).not.toContain("?request=");

    const cards = readFileSync(join(dir, "PurchaseRequestsCards.tsx"), "utf8");
    expect(cards).toContain("SuppliesPersonIdentity");

    const config = readFileSync(join(dir, "purchaseRequestsTableConfig.ts"), "utf8");
    expect(config).toContain("supplies:purchase-requests:column-prefs:v1");
    expect(config).not.toContain("purchase-orders");
  });

  it("Cards esconde Fonte/Colunas e usa metadata sem colunas", () => {
    const table = readFileSync(join(dir, "PurchaseRequestsListTable.tsx"), "utf8");
    expect(table).toMatch(/showCards[\s\S]*C\.cardsMeta\(total\)/);
    expect(table).toMatch(/!showCards[\s\S]*SuppliesTableFontSizeControls/);
    expect(table).toMatch(/!showCards[\s\S]*SuppliesTableColumnVisibilityMenu/);
    expect(table).toContain("canExport");
    expect(table).toContain("SuppliesDataCardsSortBar");
    expect(table).toContain("SuppliesCompactPagination");
    // Font style only on table region, not on cards sort bar.
    expect(table).not.toMatch(/SuppliesDataCardsSortBar[\s\S]{0,80}style=\{tableStyle\}/);

    const content = readFileSync(join(dir, "content.ts"), "utf8");
    expect(content).toContain("cardsMeta:");
    expect(content).toMatch(/cardsMeta: \(rows: number\) =>/);
  });

  it("CSS não recria botão/filtro do kit e usa região de tabela compartilhada", () => {
    const css = readFileSync(join(dir, "../../index.css"), "utf8");
    expect(css).not.toMatch(/sp-purchase-requests__btn\b/);
    expect(css).not.toMatch(/sp-purchase-requests__hero\b/);
    expect(css).toMatch(/sp-list-table-region/);
    expect(css).toMatch(/sp-list-filters/);
    expect(css).toMatch(/sp-purchase-request-detail/);
  });

  it("query Todas vs API effective + sibling + negative", () => {
    const defaults = createDefaultQuery();
    expect(defaults.branches).toEqual([]);

    const scoped = { ...defaults, branches: ["01"], request_number: "100", overall_stages: ["awaiting_order" as const] };
    const params = buildListSearchParams(scoped);
    expect(params.getAll("branch")).toEqual(["01"]);
    expect(params.get("request_number")).toBe("100");

    expect(authorizeQueryBranches(defaults, ["01", "02"]).branches).toEqual(["01", "02"]);
    expect(authorizeQueryBranches({ ...defaults, branches: ["01"] }, ["01", "02"]).branches).toEqual([
      "01",
    ]);

    const emptyUrl = parseQueryFromSearch("?page=1", ["01", "02"]);
    expect(emptyUrl.branches).toEqual([]);

    const both = parseQueryFromSearch("?branch=01&branch=02", ["01", "02"]);
    expect(both.branches).toEqual([]);

    const single = parseQueryFromSearch("?branch=02&request=02:200", ["01", "02"]);
    expect(single.branches).toEqual(["02"]);
    expect(parseRequestKey(single.request)).toEqual({
      branch: "02",
      requestNumber: "200",
    });
    expect(buildUrlSearch(single)).toContain("branch=02");
    expect(buildUrlSearch(single)).toContain("request=02%3A200");

    const sorted = parseQueryFromSearch(
      "?branch=01&sort_by=issue_date&sort_dir=asc",
      ["01", "02"],
    );
    expect(sorted.branches).toEqual(["01"]);
    expect(sorted.sort_by).toBe("issue_date");

    const stageSort = parseQueryFromSearch(
      "?sort_by=overall_stage&sort_dir=desc",
      ["01"],
    );
    expect(stageSort.sort_by).toBe("overall_stage");
    expect(stageSort.sort_dir).toBe("desc");

    const productSort = parseQueryFromSearch(
      "?sort_by=product_code&sort_dir=asc",
      ["01"],
    );
    expect(productSort.sort_by).toBe("product_code");

    expect(parseRequestKey("invalid")).toBeNull();
    expect(buildRequestKey("01", "100")).toBe("01:100");
    expect(parseQueryFromSearch("?overall_stage=not-a-stage", ["01"]).overall_stages).toEqual([]);
  });

  it("matriz de sort UI→API cobre item, produto e stage", async () => {
    const { nextServerSort, PURCHASE_REQUESTS_SORTABLE_COLUMNS, tableSortKey } = await import(
      "./query"
    );
    expect(PURCHASE_REQUESTS_SORTABLE_COLUMNS.request_item).toBe("request_item");
    expect(PURCHASE_REQUESTS_SORTABLE_COLUMNS.product).toBe("product_code");
    expect(PURCHASE_REQUESTS_SORTABLE_COLUMNS.stage).toBe("overall_stage");
    expect(PURCHASE_REQUESTS_SORTABLE_COLUMNS.opened).toBe("issue_date");
    expect(tableSortKey("overall_stage")).toBe("stage");
    expect(tableSortKey("product_code")).toBe("product");
    expect(nextServerSort(createDefaultQuery(), "stage")).toEqual({
      sort_by: "overall_stage",
      sort_dir: "asc",
      page: 1,
    });
    expect(nextServerSort(createDefaultQuery(), "product")).toEqual({
      sort_by: "product_code",
      sort_dir: "asc",
      page: 1,
    });
    expect(nextServerSort(createDefaultQuery(), "unknown")).toBeNull();
  });

  it("mapeia 403 positive/sibling e preserva mensagem genérica (negative)", () => {
    expect(mapPurchaseRequestsFetchError("403 Forbidden")).toMatch(/unidade/i);
    expect(mapPurchaseRequestsFetchError("Request failed with status 403")).toMatch(/unidade/i);
    expect(mapPurchaseRequestsFetchError("timeout upstream")).toBe("timeout upstream");
  });

  it("mapeia 422 de ordenação por situação para recorte menor (positive/sibling/negative)", () => {
    expect(
      mapPurchaseRequestsFetchError(
        "Ordenação por situação exige um recorte menor. Reduza o período ou selecione uma unidade.",
      ),
    ).toMatch(/recorte menor/i);
    expect(
      mapPurchaseRequestsFetchError(
        "[upstream_client_error] Ordenação por situação exige um recorte menor. Reduza o período ou selecione uma unidade.",
      ),
    ).toMatch(/recorte menor/i);
    expect(mapPurchaseRequestsFetchError("timeout upstream")).toBe("timeout upstream");
  });
});
