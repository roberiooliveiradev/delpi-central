import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  classifyPurchaseOrderDetailError,
  mapPurchaseOrdersFetchError,
} from "./content";
import {
  authorizeQueryBranches,
  buildListSearchParams,
  buildOrderKey,
  buildUrlSearch,
  createDefaultQuery,
  nextServerSort,
  parseOrderKey,
  parseQueryFromSearch,
} from "./query";

const dir = dirname(fileURLToPath(import.meta.url));

function collectSourceFiles(root: string): string[] {
  const entries = readdirSync(root);
  const files: string[] = [];
  for (const entry of entries) {
    const full = join(root, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      files.push(...collectSourceFiles(full));
      continue;
    }
    if (/\.(ts|tsx)$/.test(entry) && !/\.(test|spec)\.(ts|tsx)$/.test(entry)) {
      files.push(full);
    }
  }
  return files;
}

describe("PurchaseOrders feature", () => {
  it("App liga lista e ficha real em vez do placeholder", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/PurchaseOrdersPage/);
    expect(app).toMatch(/PurchaseOrderDetailPage/);
    expect(app).not.toMatch(/purchase_orders: \{\s*title: "Pedidos de compra"/);
  });

  it("cliente fala só com supplies-api", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/suppliesApiUrl\(`\/purchase-orders/);
    expect(api).toMatch(/getPurchaseOrder/);
    expect(api).toMatch(/exportPurchaseOrders/);
    expect(api).toMatch(/\/purchase-orders\/export/);
    expect(api).not.toMatch(/api-delpi/);
    expect(api).not.toMatch(/apiDelpiUrl/);
    expect(api).not.toMatch(/purchase-requests-api/);
  });

  it("nenhum runtime do MFE aponta api-delpi ou purchase-requests-api", () => {
    const srcRoot = join(dir, "../..");
    for (const file of collectSourceFiles(srcRoot)) {
      const text = readFileSync(file, "utf8");
      expect(text).not.toMatch(/api-delpi/);
      expect(text).not.toMatch(/purchase-requests-api/);
    }
  });

  it("usa PageHero, auto-filtros, refresh e SectionCard", () => {
    const page = readFileSync(join(dir, "PurchaseOrdersPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("PurchaseOrdersFilters");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("mapPurchaseOrdersFetchError");
    expect(page).toContain("buildPurchaseOrderDetailPath");
    expect(page).toContain("SuppliesScopeChipBar");
    expect(page).toContain("lastUpdatedAt");
    expect(page).toContain("canonicalizeUiBranches");
    expect(page).toContain("exportQuery");
    expect(page).toContain("PurchaseOrdersListTable");
    expect(page).toContain("highlights=");
    expect(page).toContain("C.heroOpenLines");
    expect(page).toContain("C.heroOpenValue");
    expect(page).toContain("C.heroLate");
    expect(page).toContain("summary.total_lines");
    expect(page).toContain("summary.late_lines");
    expect(page).toContain("attentionAllWithCount");
    expect(page).toContain("attentionLateWithCount");
    expect(page).toContain("isPurchaseOrderSummary");
    expect(page).not.toContain("onApply");
    expect(page).not.toContain("applyFilters");
    expect(page).not.toContain("detailComingSoon");
    expect(page).not.toContain("<select");
    expect(page).not.toContain('type="date"');

    const filters = readFileSync(join(dir, "PurchaseOrdersFilters.tsx"), "utf8");
    expect(filters).toContain("SuppliesFilterBarShell");
    expect(filters).toContain("sp-filter-bar__header");
    expect(filters).toContain("C.moreFilters");
    expect(filters).toContain("C.lessFilters");
    expect(filters).toContain("SuppliesClearFiltersButton");
    expect(filters).toContain("hasActivePurchaseOrdersFilters");
    expect(filters).toContain("buildSuppliesUnitOptions");
    expect(filters).toContain("SuppliesMultiSelectField");
    expect(filters).toContain("SUPPLIES_UNIT_FILTER_LABEL");
    expect(filters).toContain("canonicalizeUiBranches");
    expect(filters).not.toContain("searchable={unitOptions.length > 4}");
    expect(filters).toContain("useCommittedTextFilter");
    expect(filters).toContain("SP_HELP.purchaseOrdersFilters");
    expect(filters).not.toContain("Santa Catarina (01)");
    expect(filters).not.toContain("Aplicar filtros");
    expect(filters).not.toContain("onApply");
    expect(filters).not.toContain("sp-list-filters__hint");
    expect(filters).not.toContain("SuppliesSelectField");

    const types = readFileSync(join(dir, "types.ts"), "utf8");
    expect(types).toContain("PurchaseOrderListSummary");
    expect(types).toContain("total_open_value");
    expect(types).toContain("on_time_lines");
    expect(types).toContain("no_date_lines");
    expect(types).toContain("branches: string[]");
  });

  it("hero e chips usam summary server-side sem derivar de items", () => {
    const page = readFileSync(join(dir, "PurchaseOrdersPage.tsx"), "utf8");
    expect(page).toMatch(/setSummary\(isPurchaseOrderSummary/);
    expect(page).toContain("formatMoneyBr(summary.total_open_value)");
    expect(page).toContain("C.attentionAllWithCount(summary.total_lines)");
    expect(page).toContain("C.attentionLateWithCount(summary.late_lines)");
    expect(page).not.toMatch(/summary\.total_lines\s*\?\?/);
    expect(page).not.toMatch(/total_lines\s*\?\?\s*items/);
    const highlightsBlock = page.match(
      /const highlights = useMemo\(\(\) => \{[\s\S]*?\}, \[summary\]\);/,
    )?.[0];
    const chipsBlock = page.match(
      /const attentionChips = useMemo\(\(\) => \{[\s\S]*?\}, \[patchQuery, query\.late_only, summary\]\);/,
    )?.[0];
    expect(highlightsBlock).toBeTruthy();
    expect(chipsBlock).toBeTruthy();
    expect(highlightsBlock).not.toMatch(/items/);
    expect(chipsBlock).not.toMatch(/items/);
    expect(page).not.toMatch(/reduce\(/);
    expect(page).not.toContain("api-delpi");
  });

  it("toolbar usa DataTable canônico, Excel, cards e sort server-side", () => {
    const table = readFileSync(join(dir, "PurchaseOrdersListTable.tsx"), "utf8");
    expect(table).toContain("SuppliesDataListToolbar");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("C.tableMeta");
    expect(table).toContain("SuppliesEntityLink");
    expect(table).toContain("buildPurchaseOrderDetailPath");
    expect(table).toContain("headerHint");
    expect(table).toContain('align: "right"');
    expect(table).toContain("SuppliesTableFontSizeControls");
    expect(table).toContain("SuppliesCompactPagination");
    expect(table).toContain("sp-list-table-region");
    expect(table).toContain("ExcelExportButton");
    expect(table).toContain("exportPurchaseOrders");
    expect(table).toContain("PurchaseOrdersCards");
    expect(table).toContain("usePersistedViewLayout");
    expect(table).toContain("onSortChange");
    expect(table).toContain("nextServerSort");
    expect(table).not.toMatch(/rows\.sort\(/);
    expect(table).toContain("enableColumnReorder");
    expect(table).toContain("applyVisibleOrder");

    const cards = readFileSync(join(dir, "PurchaseOrdersCards.tsx"), "utf8");
    expect(cards).toContain("SuppliesDataCardsGrid");
    expect(cards).toContain("buildPurchaseOrderDetailPath");

    const config = readFileSync(join(dir, "purchaseOrdersTableConfig.ts"), "utf8");
    expect(config).toContain("supplies:purchase-orders:column-prefs:v1");
    expect(config).toContain("supplies:purchase-orders:table-font-size:v1");
    expect(config).toContain("supplies:purchase-orders:view-layout:v1");
    expect(config).not.toContain("purchase-requests");
  });

  it("ficha cobre loading, 403, 404, retry e receipts vazios", () => {
    const page = readFileSync(join(dir, "PurchaseOrderDetailPage.tsx"), "utf8");
    expect(page).toContain("SuppliesLoadingCard");
    expect(page).toContain("classifyPurchaseOrderDetailError");
    expect(page).toContain("C.retry");
    expect(page).toContain('errorKind === "forbidden"');
    expect(page).toContain("C.receiptsEmpty");
    expect(page).toContain("formatSuppliesUnitLabel");
    expect(page).toContain("SP_HELP.purchaseOrderDetail");
    expect(page).toContain("sp-purchase-order-detail__item-card");
    expect(page).toContain("C.receiptsTableScrollRegion");
    expect(page).toMatch(/role=\"region\"/);
    expect(page).not.toContain("api-delpi");
    expect(page).not.toContain("detailComingSoon");
  });

  it("lista e ficha usam scroll horizontal intencional na tabela", () => {
    const list = readFileSync(join(dir, "PurchaseOrdersListTable.tsx"), "utf8");
    expect(list).toContain("sp-list-table-region");
    expect(list).toContain("C.tableScrollRegion");
    expect(list).toContain("SuppliesDataTable");
    expect(list).toMatch(/layout=\"section\"/);

    const page = readFileSync(join(dir, "PurchaseOrdersPage.tsx"), "utf8");
    expect(page).toContain("PurchaseOrdersListTable");
    expect(page).not.toContain("api-delpi");

    const css = readFileSync(join(dir, "../../index.css"), "utf8");
    expect(css).toMatch(/\.sp-list-table-region/);
    expect(css).toMatch(/\.sp-purchase-orders__cards/);
    expect(css).toMatch(
      /\.sp-purchase-order-detail__item-card[\s\S]*overflow-wrap:\s*anywhere/,
    );
    expect(css).toMatch(
      /\.sp-purchase-order-detail__item-meta[\s\S]*minmax\(min\(100%,\s*9rem\),\s*1fr\)/,
    );
    expect(css).not.toMatch(/body\s*\{[^}]*overflow-x:\s*hidden/s);
    expect(css).not.toMatch(
      /\.dashboard-supplies-portal\s*\{[^}]*overflow-x:\s*hidden/s,
    );
  });

  it("query Todas vs API effective + sibling + negative", () => {
    const defaults = createDefaultQuery();
    expect(defaults.branches).toEqual([]);
    const query = { ...defaults, branches: ["01"], order_number: "000123", late_only: true };
    const params = buildListSearchParams(query);
    expect(params.getAll("branch")).toEqual(["01"]);
    expect(params.get("order_number")).toBe("000123");
    expect(params.get("late_only")).toBe("true");

    const multi = { ...defaults, branches: ["01", "02"], sort_by: "open_value", sort_dir: "desc" as const };
    const multiParams = buildListSearchParams(multi);
    expect(multiParams.getAll("branch")).toEqual(["01", "02"]);
    expect(multiParams.get("sort_by")).toBe("open_value");
    expect(multiParams.get("sort_dir")).toBe("desc");

    const sibling = parseQueryFromSearch(
      "?branch=02&order=02:200&late_only=true&sort_by=supplier_name&sort_dir=asc",
      ["01", "02"],
    );
    expect(sibling.branches).toEqual(["02"]);
    expect(sibling.late_only).toBe(true);
    expect(sibling.sort_by).toBe("supplier_name");
    expect(parseOrderKey(sibling.order)).toEqual({
      branch: "02",
      orderNumber: "200",
    });
    expect(buildUrlSearch(sibling)).toContain("branch=02");
    expect(buildUrlSearch(sibling)).not.toContain("branch=01");

    const both = parseQueryFromSearch("?branch=01&branch=02", ["01", "02"]);
    expect(both.branches).toEqual([]);

    expect(parseOrderKey("invalid")).toBeNull();
    expect(buildOrderKey("01", "100")).toBe("01:100");
    expect(authorizeQueryBranches(createDefaultQuery(), ["01", "02"]).branches).toEqual([
      "01",
      "02",
    ]);

    const toggled = nextServerSort(query, "open_value");
    expect(toggled).toEqual({ sort_by: "open_value", sort_dir: "asc", page: 1 });
    expect(nextServerSort({ ...query, sort_by: "open_value", sort_dir: "asc" }, "open_value")).toEqual({
      sort_by: "open_value",
      sort_dir: "desc",
      page: 1,
    });
    expect(nextServerSort(query, "unknown")).toBeNull();
  });

  it("mapeia 403 positive/sibling e preserva mensagem genérica (negative)", () => {
    expect(mapPurchaseOrdersFetchError("403 Forbidden")).toMatch(/filial/i);
    expect(mapPurchaseOrdersFetchError("Request failed with status 403")).toMatch(/filial/i);
    expect(mapPurchaseOrdersFetchError("timeout upstream")).toBe("timeout upstream");
  });

  it("classifica erro da ficha 403/404/genérico", () => {
    expect(classifyPurchaseOrderDetailError("[forbidden] Forbidden").kind).toBe("forbidden");
    expect(classifyPurchaseOrderDetailError("[not_found] Not Found").kind).toBe("not_found");
    expect(classifyPurchaseOrderDetailError("timeout upstream").kind).toBe("error");
  });
});
