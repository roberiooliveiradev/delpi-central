import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { mapPurchaseOrdersFetchError } from "./content";
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
  it("App liga a página real em vez do placeholder", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/PurchaseOrdersPage/);
    expect(app).not.toMatch(/purchase_orders: \{\s*title: "Pedidos de compra"/);
  });

  it("cliente fala só com supplies-api", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/suppliesApiUrl\(`\/purchase-orders/);
    expect(api).not.toMatch(/api-delpi/);
  });

  it("usa PageHero, FilterBar kit e SectionCard", () => {
    const page = readFileSync(join(dir, "PurchaseOrdersPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("PurchaseOrdersFilters");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("mapPurchaseOrdersFetchError");
    expect(page).not.toContain("<select");
    expect(page).not.toContain('type="date"');

    const filters = readFileSync(join(dir, "PurchaseOrdersFilters.tsx"), "utf8");
    expect(filters).toContain("SuppliesFilterBarShell");
    expect(filters).toContain("SuppliesDateField");
    expect(filters).toContain("SuppliesSelectField");
    expect(filters).toContain("SP_HELP.purchaseOrdersBranch");
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
});
