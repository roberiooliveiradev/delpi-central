import { afterEach, describe, expect, it, vi } from "vitest";

import * as httpClient from "./httpClient";
import {
  fetchSafetyStockFilters,
  fetchSafetyStockItemDetails,
  fetchSafetyStockItemSuppliers,
  fetchSafetyStockItems,
  fetchSafetyStockSummary,
  fetchSafetyStockSupplierPriceHistory,
} from "./safetyStockApi";
import { HTTP_CALLER_APP } from "./httpClient";

describe("safetyStockApi", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("envia parâmetros camelCase e header do caller", async () => {
    const spy = vi.spyOn(httpClient, "httpGet").mockResolvedValue({
      success: true,
      data: {
        branch: "01",
        product_groups: [],
        units: [],
        statuses: [],
        warehouses: ["01"],
        primary_warehouse: "01",
        work_in_process_warehouses: ["50", "98", "99"],
        work_in_process_note: "",
        authorized_branches: ["01"],
      },
    });

    await fetchSafetyStockFilters("01", false);

    expect(spy).toHaveBeenCalledWith(
      "/apps/api-delpi/supplies/safety-stock/filters?branch=01&includeBlocked=false",
      expect.any(Object),
    );
    expect(HTTP_CALLER_APP).toBe("estoque-seguranca");
  });

  it("monta query de summary com filtros opcionais", async () => {
    const spy = vi.spyOn(httpClient, "httpGet").mockResolvedValue({
      success: true,
      data: {
        total_materials: 0,
        with_safety_stock: 0,
        without_safety_stock: 0,
        below_safety_stock: 0,
        at_safety_stock: 0,
        above_safety_stock: 0,
        with_primary_stock: 0,
        without_primary_stock: 0,
        with_work_in_process_stock: 0,
        deficit_by_unit: [],
      },
    });

    await fetchSafetyStockSummary({
      branch: "01",
      includeBlocked: false,
      productGroup: "",
      unit: "",
      search: "10010005",
      status: "below_safety_stock",
      includeWithoutSafetyStock: true,
      sortBy: "product_code",
      sortDirection: "asc",
    });

    const url = String(spy.mock.calls[0]?.[0]);
    expect(url).toContain("branch=01");
    expect(url).toContain("search=10010005");
    expect(url).toContain("status=below_safety_stock");
    expect(url).toContain("includeWithoutSafetyStock=true");
  });

  it("monta query paginada de items", async () => {
    const spy = vi.spyOn(httpClient, "httpGet").mockResolvedValue({
      success: true,
      data: {
        items: [],
        page: 2,
        page_size: 25,
        total: 0,
        total_pages: 0,
        sort_by: "product_code",
        sort_direction: "asc",
      },
    });

    await fetchSafetyStockItems(
      {
        branch: "02",
        includeBlocked: true,
        productGroup: "",
        unit: "",
        search: "",
        status: "",
        includeWithoutSafetyStock: false,
        sortBy: "primary_stock",
        sortDirection: "desc",
      },
      2,
      25,
    );

    const url = String(spy.mock.calls[0]?.[0]);
    expect(url).toContain("branch=02");
    expect(url).toContain("page=2");
    expect(url).toContain("pageSize=25");
    expect(url).toContain("sortBy=primary_stock");
    expect(url).toContain("sortDirection=desc");
    expect(url).toContain("includeBlocked=true");
  });

  it("monta URL de detalhe com código codificado", async () => {
    const spy = vi.spyOn(httpClient, "httpGet").mockResolvedValue({
      success: true,
      data: {
        product: { product_code: "10010005" },
        stock: {},
        purchase_coverage: { status: "none" },
        open_purchase_orders: { items: [], total: 0 },
        open_commitments: { items: [], total: 0 },
        stock_projection: { items: [], total: 0, summary: { status: "sufficient" } },
      },
    });

    await fetchSafetyStockItemDetails("01", "10010005");

    expect(String(spy.mock.calls[0]?.[0])).toBe(
      "/apps/api-delpi/supplies/safety-stock/items/10010005/details?branch=01",
    );
  });

  it("monta URL de fornecedores vinculados com código codificado", async () => {
    const spy = vi.spyOn(httpClient, "httpGet").mockResolvedValue({
      success: true,
      data: { items: [], total: 0 },
    });

    await fetchSafetyStockItemSuppliers("01", "100 10005");

    expect(String(spy.mock.calls[0]?.[0])).toBe(
      "/apps/api-delpi/supplies/safety-stock/items/100%2010005/suppliers?branch=01",
    );
  });

  it("monta URL de histórico de preço por fornecedor", async () => {
    const spy = vi.spyOn(httpClient, "httpGet").mockResolvedValue({
      success: true,
      data: {
        product_code: "10010005",
        branch: "01",
        supplier_code: "F001",
        supplier_store: "01",
        items: [],
        total: 0,
        summary: { total_purchases: 0 },
      },
    });

    await fetchSafetyStockSupplierPriceHistory("01", "10010005", "F001", "01");

    expect(String(spy.mock.calls[0]?.[0])).toBe(
      "/apps/api-delpi/supplies/safety-stock/items/10010005/suppliers/F001/purchase-price-history?branch=01&supplierStore=01",
    );
  });
});
