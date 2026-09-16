import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  classifyPurchaseOrderDetailError,
  mapPurchaseOrdersFetchError,
} from "./content";
import {
  buildListSearchParams,
  buildOrderKey,
  buildUrlSearch,
  createDefaultQuery,
  parseOrderKey,
  parseQueryFromSearch,
} from "./query";

const dir = dirname(fileURLToPath(import.meta.url));

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
    expect(api).not.toMatch(/api-delpi/);
    expect(api).not.toMatch(/apiDelpiUrl/);
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
    expect(page).toContain("resolveDefaultBranch");
    expect(page).toContain("PurchaseOrdersListTable");
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
    expect(filters).toContain("useCommittedTextFilter");
    expect(filters).toContain("SP_HELP.purchaseOrdersFilters");
    expect(filters).not.toContain("Aplicar filtros");
    expect(filters).not.toContain("onApply");
    expect(filters).not.toContain("sp-list-filters__hint");
    expect(filters).not.toContain("SuppliesSegmentToggle");
  });

  it("toolbar usa DataTable canônico, metadata e link PC", () => {
    const table = readFileSync(join(dir, "PurchaseOrdersListTable.tsx"), "utf8");
    expect(table).toContain("SuppliesDataListToolbar");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("C.tableMeta");
    expect(table).toContain("SuppliesEntityLink");
    expect(table).toContain("buildPurchaseOrderDetailPath");
    expect(table).toContain("headerHint");
    expect(table).toContain("align: \"right\"");
    expect(table).toContain("SuppliesTableFontSizeControls");
    expect(table).toContain("SuppliesCompactPagination");
    expect(table).toContain("sp-list-table-region");
    expect(table).not.toContain("Excel");
    expect(table).not.toMatch(/\bonExport\b/);
    expect(table).not.toMatch(/downloadPurchaseOrdersExport/);

    const config = readFileSync(join(dir, "purchaseOrdersTableConfig.ts"), "utf8");
    expect(config).toContain("supplies:purchase-orders:column-prefs:v1");
    expect(config).toContain("supplies:purchase-orders:table-font-size:v1");
  });

  it("ficha cobre loading, 403, 404, retry e receipts vazios", () => {
    const page = readFileSync(join(dir, "PurchaseOrderDetailPage.tsx"), "utf8");
    expect(page).toContain("SuppliesLoadingCard");
    expect(page).toContain("classifyPurchaseOrderDetailError");
    expect(page).toContain("C.retry");
    expect(page).toContain("errorKind === \"forbidden\"");
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

  it("query positive + sibling + negative", () => {
    const query = createDefaultQuery("01");
    query.order_number = "000123";
    query.late_only = true;
    const params = buildListSearchParams(query);
    expect(params.get("branch")).toBe("01");
    expect(params.get("order_number")).toBe("000123");
    expect(params.get("late_only")).toBe("true");

    const sibling = parseQueryFromSearch("?branch=02&order=02:200&late_only=true", "01");
    expect(sibling.branch).toBe("02");
    expect(sibling.late_only).toBe(true);
    expect(parseOrderKey(sibling.order)).toEqual({
      branch: "02",
      orderNumber: "200",
    });
    expect(buildUrlSearch(sibling)).toContain("branch=02");

    expect(parseOrderKey("invalid")).toBeNull();
    expect(buildOrderKey("01", "100")).toBe("01:100");
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
