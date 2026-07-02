import { describe, expect, it } from "vitest";

import {
  buildFiltrosQuery,
  buildLancamentosQuery,
  buildRankingCentrosQuery,
  buildRankingFornecedoresQuery,
  buildResumoQuery,
} from "./queryParams";

const baseFilters = {
  startDate: "2025-07-01",
  endDate: "2026-06-30",
  branch: "01",
  costCenter: "0101",
  supplierCode: "003287",
  supplierStore: "01",
};

describe("queryParams", () => {
  it("filtros envia cost_center para restringir fornecedores", () => {
    const params = buildFiltrosQuery({
      ...baseFilters,
      supplierCode: "003287",
      supplierStore: "01",
    });

    expect(params.get("cost_center")).toBe("0101");
    expect(params.get("supplier_code")).toBeNull();
    expect(params.get("supplier_store")).toBeNull();
  });

  it("monta resumo com todos os filtros opcionais", () => {
    const params = buildResumoQuery(baseFilters);

    expect(params.get("start_date")).toBe("2025-07-01");
    expect(params.get("end_date")).toBe("2026-06-30");
    expect(params.get("branch")).toBe("01");
    expect(params.get("cost_center")).toBe("0101");
    expect(params.get("supplier_code")).toBe("003287");
    expect(params.get("supplier_store")).toBe("01");
  });

  it("ranking-centros não envia cost_center", () => {
    const params = buildRankingCentrosQuery(baseFilters, 10);

    expect(params.get("cost_center")).toBeNull();
    expect(params.get("supplier_code")).toBe("003287");
    expect(params.get("supplier_store")).toBe("01");
    expect(params.get("limit")).toBe("10");
  });

  it("ranking-fornecedores não envia supplier_code nem supplier_store", () => {
    const params = buildRankingFornecedoresQuery(baseFilters, 10);

    expect(params.get("cost_center")).toBe("0101");
    expect(params.get("supplier_code")).toBeNull();
    expect(params.get("supplier_store")).toBeNull();
    expect(params.get("limit")).toBe("10");
  });

  it("lancamentos respeita paginação e ordenação padrão", () => {
    const params = buildLancamentosQuery({
      ...baseFilters,
      page: 1,
      pageSize: 50,
      sortBy: "data_emissao",
      sortDir: "desc",
    });

    expect(params.get("page")).toBe("1");
    expect(params.get("page_size")).toBe("50");
    expect(params.get("sort_by")).toBe("data_emissao");
    expect(params.get("sort_dir")).toBe("desc");
  });
});
