import { describe, expect, it } from "vitest";

import {
  detailMatchesTarget,
  isSafetyStockFiltersResponse,
  isSafetyStockItemDetail,
  isSafetyStockItemsResponse,
  isSafetyStockSummary,
  isSafetyStockSuppliersResponse,
} from "./api";
import {
  buildItemsSearchParams,
  buildScopeFilterParams,
  buildUrlSearch,
  createDefaultQuery,
  formatQuantity,
  nextServerSort,
  normalizeBranchScope,
  normalizeSortDirection,
  normalizeSortField,
  normalizeStatus,
  parseDetailTargetFromSearch,
  parseQueryFromSearch,
  sameSafetyStockQuery,
} from "./query";
import { labelSafetyStockStatus, statusBadgeVariant } from "./content";
import { SAFETY_STOCK_SORT_FIELDS } from "./types";

describe("safety stock query defaults", () => {
  it("default = branch all + sortBy product_code asc + page 1 size 50", () => {
    const q = createDefaultQuery();
    expect(q.branch).toBe("all");
    expect(q.status).toBe("");
    expect(q.includeBlocked).toBe(false);
    expect(q.includeWithoutSafetyStock).toBe(true);
    expect(q.sortBy).toBe("product_code");
    expect(q.sortDirection).toBe("asc");
    expect(q.page).toBe(1);
    expect(q.page_size).toBe(50);
  });
});

describe("safety stock BFF params", () => {
  it("branch=all envia escopo único, sem fan-out", () => {
    const params = buildItemsSearchParams(createDefaultQuery());
    expect(params.getAll("branch")).toEqual(["all"]);
  });

  it("branch=01 e branch=02 são enviados como escopo único", () => {
    for (const branch of ["01", "02"] as const) {
      const params = buildItemsSearchParams({
        ...createDefaultQuery(),
        branch,
      });
      expect(params.getAll("branch")).toEqual([branch]);
    }
  });

  it("filtros e sort usam camelCase do contrato BFF", () => {
    const q = {
      ...createDefaultQuery(),
      branch: "02" as const,
      status: "below_safety_stock" as const,
      productGroup: "MP",
      unit: "UN",
      search: "resina",
      includeBlocked: true,
      includeWithoutSafetyStock: false,
      sortBy: "deficit_quantity" as const,
      sortDirection: "desc" as const,
      page: 3,
      page_size: 200,
    };
    const params = buildItemsSearchParams(q);
    expect(params.get("productGroup")).toBe("MP");
    expect(params.get("unit")).toBe("UN");
    expect(params.get("search")).toBe("resina");
    expect(params.get("status")).toBe("below_safety_stock");
    expect(params.get("includeBlocked")).toBe("true");
    expect(params.get("includeWithoutSafetyStock")).toBe("false");
    expect(params.get("sortBy")).toBe("deficit_quantity");
    expect(params.get("sortDirection")).toBe("desc");
    expect(params.get("page")).toBe("3");
    expect(params.get("page_size")).toBe("200");
    expect(params.get("sort_by")).toBeNull();
    expect(params.get("product_group")).toBeNull();
  });

  it("summary/summary-scope não leva paginação nem sort", () => {
    const params = buildScopeFilterParams(createDefaultQuery());
    expect(params.get("page")).toBeNull();
    expect(params.get("sortBy")).toBeNull();
    expect(params.get("branch")).toBe("all");
  });
});

describe("safety stock URL state", () => {
  it("round-trip A → B → A restaura o estado (deep link / F5 / voltar)", () => {
    const a = createDefaultQuery();
    const b = {
      ...createDefaultQuery(),
      branch: "02" as const,
      status: "below_safety_stock" as const,
      productGroup: "MP",
      search: "resina",
      includeBlocked: true,
      sortBy: "deficit_quantity" as const,
      sortDirection: "desc" as const,
      page: 4,
      page_size: 100,
    };
    const restoredA = parseQueryFromSearch(buildUrlSearch(a));
    const restoredB = parseQueryFromSearch(buildUrlSearch(b));
    expect(sameSafetyStockQuery(restoredA, a)).toBe(true);
    expect(sameSafetyStockQuery(restoredB, b)).toBe(true);
  });

  it("URL inválida recupera com defaults previsíveis", () => {
    const q = parseQueryFromSearch(
      "?branch=99&status=weird&sortBy=hack&sortDirection=sideways&page=-2&page_size=9999&includeBlocked=maybe",
    );
    expect(q.branch).toBe("all");
    expect(q.status).toBe("");
    expect(q.sortBy).toBe("product_code");
    expect(q.sortDirection).toBe("asc");
    expect(q.page).toBe(1);
    expect(q.page_size).toBe(50);
    expect(q.includeBlocked).toBe(false);
  });

  it("includeWithoutSafetyStock=false persiste; default true omite", () => {
    const off = { ...createDefaultQuery(), includeWithoutSafetyStock: false };
    expect(buildUrlSearch(off)).toContain("includeWithoutSafetyStock=false");
    expect(buildUrlSearch(createDefaultQuery())).not.toContain(
      "includeWithoutSafetyStock",
    );
    expect(
      parseQueryFromSearch("?includeWithoutSafetyStock=false")
        .includeWithoutSafetyStock,
    ).toBe(false);
  });
});

describe("safety stock normalization", () => {
  it("branch scope aceita só all|01|02", () => {
    expect(normalizeBranchScope("all")).toBe("all");
    expect(normalizeBranchScope("01")).toBe("01");
    expect(normalizeBranchScope("02")).toBe("02");
    expect(normalizeBranchScope("03")).toBe("all");
    expect(normalizeBranchScope("")).toBe("all");
  });

  it("status aceita só os quatro canônicos", () => {
    expect(normalizeStatus("below_safety_stock")).toBe("below_safety_stock");
    expect(normalizeStatus("outro")).toBe("");
  });

  it("sortBy aceita só a allowlist de nove campos", () => {
    for (const field of SAFETY_STOCK_SORT_FIELDS) {
      expect(normalizeSortField(field)).toBe(field);
    }
    expect(normalizeSortField("product_id")).toBe("product_code");
  });

  it("sortDirection só asc|desc", () => {
    expect(normalizeSortDirection("desc")).toBe("desc");
    expect(normalizeSortDirection("ASC")).toBe("asc");
    expect(normalizeSortDirection("nope")).toBe("asc");
  });
});

describe("safety stock sort", () => {
  it("mesmo campo alterna direção e volta à página 1", () => {
    const q = {
      ...createDefaultQuery(),
      sortBy: "deficit_quantity" as const,
      sortDirection: "asc" as const,
      page: 5,
    };
    expect(nextServerSort(q, "deficit_quantity")).toEqual({
      sortBy: "deficit_quantity",
      sortDirection: "desc",
      page: 1,
    });
  });

  it("numérico novo abre desc; textual abre asc; fora da allowlist retorna null", () => {
    const q = createDefaultQuery();
    expect(nextServerSort(q, "deficit_quantity")).toEqual({
      sortBy: "deficit_quantity",
      sortDirection: "desc",
      page: 1,
    });
    expect(nextServerSort(q, "product_description")).toEqual({
      sortBy: "product_description",
      sortDirection: "asc",
      page: 1,
    });
    expect(nextServerSort(q, "not_a_field")).toBeNull();
  });
});

describe("safety stock payload guards (residual de envelope E11.S1)", () => {
  const validSummary = {
    total_materials: 10,
    with_safety_stock: 8,
    without_safety_stock: 2,
    below_safety_stock: 3,
    at_safety_stock: 1,
    above_safety_stock: 4,
    with_primary_stock: 6,
    without_primary_stock: 4,
    with_work_in_process_stock: 5,
    deficit_by_unit: [{ unit: "UN", material_count: 3, deficit_quantity: 12.5 }],
  };

  it("summary válido passa; null/lista/campo ausente falham", () => {
    expect(isSafetyStockSummary(validSummary)).toBe(true);
    expect(isSafetyStockSummary(null)).toBe(false);
    expect(isSafetyStockSummary([])).toBe(false);
    expect(isSafetyStockSummary({})).toBe(false);
    expect(
      isSafetyStockSummary({ ...validSummary, deficit_by_unit: "x" }),
    ).toBe(false);
  });

  it("items válido passa; data null/sem items falham", () => {
    expect(
      isSafetyStockItemsResponse({ items: [], total: 0, page: 1 }),
    ).toBe(true);
    expect(isSafetyStockItemsResponse(null)).toBe(false);
    expect(isSafetyStockItemsResponse({ items: "x", total: 0, page: 1 })).toBe(
      false,
    );
    expect(isSafetyStockItemsResponse({ items: [] })).toBe(false);
  });

  it("filters válido exige branch_catalog + listas de opções", () => {
    expect(
      isSafetyStockFiltersResponse({
        branch: "all",
        branch_catalog: ["01", "02"],
        all_scope: "all",
        product_groups: [],
        units: ["UN"],
        statuses: [],
      }),
    ).toBe(true);
    expect(isSafetyStockFiltersResponse({ branch_catalog: [] })).toBe(false);
    expect(isSafetyStockFiltersResponse(null)).toBe(false);
  });
});

describe("safety stock presentation", () => {
  it("status tem rótulo PT-BR e variante não-neutra para abaixo", () => {
    expect(labelSafetyStockStatus("below_safety_stock")).toMatch(/Abaixo/);
    expect(labelSafetyStockStatus("without_safety_stock")).toMatch(/Sem/);
    expect(labelSafetyStockStatus(null)).toBe("—");
    expect(statusBadgeVariant("below_safety_stock")).toBe("danger");
    expect(statusBadgeVariant("at_safety_stock")).toBe("warning");
    expect(statusBadgeVariant("above_safety_stock")).toBe("neutral");
  });

  it("quantidade formata em pt-BR e preserva zero", () => {
    expect(formatQuantity(0)).toBe("0");
    expect(formatQuantity(null)).toBe("—");
    expect(formatQuantity(1234.5)).toContain("1.234");
  });
});

describe("safety stock detail target (E11.S3)", () => {
  it("URL serializa item+itemBranch junto aos filtros", () => {
    const q = { ...createDefaultQuery(), branch: "all" as const };
    const search = buildUrlSearch(q, {
      productCode: "10070821",
      branch: "01",
    });
    const params = new URLSearchParams(search.slice(1));
    expect(params.get("item")).toBe("10070821");
    expect(params.get("itemBranch")).toBe("01");
    // Filtros permanecem intactos.
    expect(params.get("page")).toBe("1");
    expect(params.get("sortBy")).toBe("product_code");
  });

  it("round-trip: deep link restaura o detalhe sem abrir material errado", () => {
    const search = buildUrlSearch(createDefaultQuery(), {
      productCode: "10070821",
      branch: "02",
    });
    expect(parseDetailTargetFromSearch(search)).toEqual({
      productCode: "10070821",
      branch: "02",
    });
  });

  it("detalhe exige filial concreta — all/vazio/inválido não abrem", () => {
    expect(
      parseDetailTargetFromSearch("?item=10070821&itemBranch=all"),
    ).toBeNull();
    expect(parseDetailTargetFromSearch("?item=10070821")).toBeNull();
    expect(
      parseDetailTargetFromSearch("?item=10070821&itemBranch=03"),
    ).toBeNull();
    expect(parseDetailTargetFromSearch("?itemBranch=01")).toBeNull();
    expect(parseDetailTargetFromSearch("")).toBeNull();
  });

  it("fechar o detalhe remove item+itemBranch e preserva filtros", () => {
    const q = {
      ...createDefaultQuery(),
      branch: "02" as const,
      status: "below_safety_stock" as const,
    };
    const search = buildUrlSearch(q, null);
    const params = new URLSearchParams(search.slice(1));
    expect(params.get("item")).toBeNull();
    expect(params.get("itemBranch")).toBeNull();
    expect(params.get("branch")).toBe("02");
    expect(params.get("status")).toBe("below_safety_stock");
  });
});

describe("safety stock detail guards (E11.S3)", () => {
  const detail = {
    product: { product_code: "10070821", branch: "01" },
    stock: { safety_stock: 10 },
  };

  it("detalhe válido exige product_code + branch concretos", () => {
    expect(isSafetyStockItemDetail(detail)).toBe(true);
    expect(isSafetyStockItemDetail({ ...detail, stock: {} })).toBe(true);
  });

  it("payload malformado ({} / null / sem identidade) é rejeitado", () => {
    expect(isSafetyStockItemDetail({})).toBe(false);
    expect(isSafetyStockItemDetail(null)).toBe(false);
    expect(isSafetyStockItemDetail({ product: {}, stock: {} })).toBe(false);
    expect(
      isSafetyStockItemDetail({
        product: { product_code: "  ", branch: "01" },
        stock: {},
      }),
    ).toBe(false);
    expect(
      isSafetyStockItemDetail({
        product: { product_code: "X", branch: "" },
        stock: {},
      }),
    ).toBe(false);
    expect(isSafetyStockItemDetail({ product: detail.product })).toBe(false);
  });

  it("identidade exata: resposta deve casar produto+filial solicitados (E11.S4)", () => {
    const target = { productCode: "10070821", branch: "01" as const };
    const match = (product: Record<string, unknown>) =>
      detailMatchesTarget(
        { ...detail, product } as Parameters<typeof detailMatchesTarget>[0],
        target,
      );

    // Positivo: mesmo produto + mesma filial.
    expect(match({ product_code: "10070821", branch: "01" })).toBe(true);
    // Produto incorreto + filial correta.
    expect(match({ product_code: "99999999", branch: "01" })).toBe(false);
    // Produto correto + filial incorreta (filial irmã não substitui).
    expect(match({ product_code: "10070821", branch: "02" })).toBe(false);
    // Ambos incorretos.
    expect(match({ product_code: "99999999", branch: "02" })).toBe(false);
  });

  it("identidade preserva zeros à esquerda — sem coerção numérica nem parcial", () => {
    const target = { productCode: "00100708", branch: "01" as const };
    const match = (code: string, branch: string) =>
      detailMatchesTarget(
        {
          ...detail,
          product: { product_code: code, branch },
        } as Parameters<typeof detailMatchesTarget>[0],
        target,
      );

    expect(match("00100708", "01")).toBe(true);
    // Zeros à esquerda são significativos: código "equivalente" sem zeros ≠.
    expect(match("100708", "01")).toBe(false);
    // Sem match parcial/prefixo.
    expect(match("0010070899", "01")).toBe(false);
    // Filial "1" não equivale a "01".
    expect(match("00100708", "1")).toBe(false);
  });

  it("fornecedores exigem items[] + total; {} vazio é rejeitado", () => {
    expect(isSafetyStockSuppliersResponse({ items: [], total: 0 })).toBe(true);
    expect(isSafetyStockSuppliersResponse({})).toBe(false);
    expect(isSafetyStockSuppliersResponse(null)).toBe(false);
    expect(isSafetyStockSuppliersResponse({ items: [] })).toBe(false);
  });
});
