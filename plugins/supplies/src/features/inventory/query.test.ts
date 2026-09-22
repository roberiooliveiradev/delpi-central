import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import {
  getInventoryStockBalancesSummary,
  listInventoryStockBalances,
} from "./api";
import { mapInventoryFetchError } from "./content";
import { hasActiveInventoryFilters } from "./hasActiveFilters";
import {
  buildItemsSearchParams,
  buildSummarySearchParams,
  buildUrlSearch,
  buildWarehouseFilterOptions,
  composeSortToken,
  createDefaultQuery,
  formatQuantity,
  formatUnitOfMeasure,
  formatWarehouseDisplay,
  nextServerSort,
  normalizeInventorySort,
  parseQueryFromSearch,
} from "./query";

describe("inventory query / API params", () => {
  it("default = Todas + sort stock_value_desc + page 1", () => {
    const q = createDefaultQuery();
    expect(q.branches).toEqual([]);
    expect(q.warehouse).toBe("");
    expect(q.sort).toBe("stock_value_desc");
    expect(q.page).toBe(1);
    expect(q.page_size).toBe(50);
  });

  it("Todas omite branch; 01/02 e 01+02 enviam branch", () => {
    const all = createDefaultQuery();
    expect(buildSummarySearchParams(all).getAll("branch")).toEqual([]);

    expect(
      buildSummarySearchParams({ ...all, branches: ["01"] }).getAll("branch"),
    ).toEqual(["01"]);
    expect(
      buildSummarySearchParams({ ...all, branches: ["02"] }).getAll("branch"),
    ).toEqual(["02"]);
    expect(
      buildSummarySearchParams({
        ...all,
        branches: ["01", "02"],
      }).getAll("branch"),
    ).toEqual(["01", "02"]);
  });

  it("não emite branch=all nem only_positive", () => {
    const qs = buildItemsSearchParams(createDefaultQuery()).toString();
    expect(qs).not.toMatch(/branch=all/);
    expect(qs).not.toMatch(/only_positive/);
    expect(qs).not.toMatch(/api-delpi/);
  });

  it("warehouse só entra quando selecionado", () => {
    const withWh = buildSummarySearchParams({
      branches: ["01"],
      warehouse: "25",
    });
    expect(withWh.get("warehouse")).toBe("25");
    const without = buildSummarySearchParams(
      { branches: ["01"], warehouse: "25" },
      { includeWarehouse: false },
    );
    expect(without.get("warehouse")).toBeNull();
  });

  it("items envia sort allowlist + paginação", () => {
    const params = buildItemsSearchParams({
      ...createDefaultQuery(),
      sort: "quantity_asc",
      page: 2,
      page_size: 100,
    });
    expect(params.get("sort")).toBe("quantity_asc");
    expect(params.get("page")).toBe("2");
    expect(params.get("page_size")).toBe("100");
  });

  it("URL round-trip preserva estado canônico", () => {
    const query = {
      branches: ["02"],
      warehouse: "01",
      sort: "product_code_asc" as const,
      page: 3,
      page_size: 100,
    };
    const parsed = parseQueryFromSearch(buildUrlSearch(query), ["01", "02"]);
    expect(parsed).toEqual(query);
  });

  it("sanitiza params inválidos sem inventar branch", () => {
    const parsed = parseQueryFromSearch(
      "?branch=99&page=-1&page_size=abc&sort=hack&warehouse=03",
      ["01", "02"],
    );
    expect(parsed.branches).toEqual([]);
    expect(parsed.page).toBe(1);
    expect(parsed.page_size).toBe(50);
    expect(parsed.sort).toBe("stock_value_desc");
    expect(parsed.warehouse).toBe("03");
  });

  it("normalizeInventorySort rejeita token arbitrário", () => {
    expect(normalizeInventorySort("hack")).toBe("stock_value_desc");
    expect(normalizeInventorySort("stock_value_asc")).toBe("stock_value_asc");
  });

  it("nextServerSort alterna direção e reseta page", () => {
    const q = createDefaultQuery();
    const next = nextServerSort(q, "stock_value");
    expect(next).toEqual({ sort: "stock_value_asc", page: 1 });
    expect(nextServerSort({ ...q, sort: "quantity_asc" }, "quantity")).toEqual({
      sort: "quantity_desc",
      page: 1,
    });
    expect(composeSortToken("product_code", "desc")).toBe("product_code_desc");
  });

  it("filtro muda → page 1 no hasActive + clear", () => {
    expect(hasActiveInventoryFilters(createDefaultQuery(), ["01", "02"])).toBe(
      false,
    );
    expect(
      hasActiveInventoryFilters(
        { ...createDefaultQuery(), branches: ["01"] },
        ["01", "02"],
      ),
    ).toBe(true);
    expect(
      hasActiveInventoryFilters(
        { ...createDefaultQuery(), warehouse: "25" },
        ["01", "02"],
      ),
    ).toBe(true);
  });
});

describe("inventory null / zero / negative presentation", () => {
  it("preserva zero e negativo no formatQuantity", () => {
    expect(formatQuantity(10)).toMatch(/10/);
    expect(formatQuantity(0)).toBe("0");
    expect(formatQuantity(-5)).toMatch(/-5/);
  });

  it("UM null → representação neutra", () => {
    expect(formatUnitOfMeasure(null)).toBe("—");
    expect(formatUnitOfMeasure("")).toBe("—");
    expect(formatUnitOfMeasure("UN")).toBe("UN");
  });

  it("warehouse label null / código vazio", () => {
    expect(formatWarehouseDisplay("03", null)).toBe("03");
    expect(formatWarehouseDisplay("", null)).toBe("Sem código");
    expect(formatWarehouseDisplay("01", "Almoxarifado")).toBe(
      "01 — Almoxarifado",
    );
  });

  it("opções de armazém deduplicam por código e ignoram vazio como filtro", () => {
    const options = buildWarehouseFilterOptions([
      { branch: "01", warehouse: "01", warehouse_label: "Almox" },
      { branch: "02", warehouse: "01", warehouse_label: "Almox" },
      { branch: "01", warehouse: "25", warehouse_label: null },
      { branch: "01", warehouse: "", warehouse_label: null },
      { branch: "01", warehouse: "03", warehouse_label: null },
    ]);
    expect(options.map((o) => o.value)).toEqual(["01", "03", "25"]);
    expect(options.find((o) => o.value === "01")?.label).toBe("01 — Almox");
    expect(options.find((o) => o.value === "25")?.label).toBe("25");
  });
});

describe("inventory API client", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("summary e items apontam só para supplies-api e sem only_positive", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({
        summary: {
          product_count: 1,
          warehouse_count: 1,
          total_stock_value: 10,
        },
        by_warehouse: [],
        items: [],
        page: 1,
        page_size: 50,
        total: 0,
      }),
    });

    await getInventoryStockBalancesSummary({
      branches: ["01", "02"],
      warehouse: "",
    });
    await listInventoryStockBalances({
      ...createDefaultQuery(),
      branches: ["01"],
      warehouse: "25",
      sort: "quantity_desc",
      page: 2,
    });

    const calls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.map(
      (c) => String(c[0]),
    );
    expect(calls[0]).toMatch(
      /^\/apps\/supplies-api\/inventory\/stock-balances\/summary\?/,
    );
    expect(calls[0]).toContain("branch=01");
    expect(calls[0]).toContain("branch=02");
    expect(calls[0]).not.toContain("warehouse=");
    expect(calls[0]).not.toContain("only_positive");
    expect(calls[0]).not.toMatch(/api-delpi/);

    expect(calls[1]).toMatch(
      /^\/apps\/supplies-api\/inventory\/stock-balances\/items\?/,
    );
    expect(calls[1]).toContain("branch=01");
    expect(calls[1]).toContain("warehouse=25");
    expect(calls[1]).toContain("sort=quantity_desc");
    expect(calls[1]).toContain("page=2");
    expect(calls[1]).not.toContain("only_positive");
    expect(calls[1]).not.toMatch(/api-delpi/);
  });
});

describe("inventory error mapping", () => {
  it("mapeia 403 sem vazar token técnico", () => {
    expect(mapInventoryFetchError("403 Forbidden")).toMatch(/filial/i);
    expect(mapInventoryFetchError("boom")).toBe("boom");
  });
});
