import { describe, expect, it } from "vitest";

import { despesasCentroCustoApiPaths } from "../api/despesasCentroCustoApi";
import {
  buildRankingCentrosQuery,
  buildRankingFornecedoresQuery,
  queryString,
} from "../utils/queryParams";

describe("despesasCentroCustoApi", () => {
  it("expõe endpoints sob o prefixo do gateway", () => {
    expect(despesasCentroCustoApiPaths.filtros).toBe(
      "/apps/api-delpi/financeiro/despesas-centro-custo/filtros",
    );
    expect(despesasCentroCustoApiPaths.lancamentos).toBe(
      "/apps/api-delpi/financeiro/despesas-centro-custo/lancamentos",
    );
  });

  it("não monta supplier em ranking-fornecedores", () => {
    const qs = queryString(
      buildRankingFornecedoresQuery(
        {
          startDate: "2025-07-01",
          endDate: "2026-06-30",
          supplierCode: "003287",
          supplierStore: "01",
        },
        10,
      ),
    );

    expect(qs).not.toContain("supplier_code");
    expect(qs).not.toContain("supplier_store");
  });

  it("não monta cost_center em ranking-centros", () => {
    const qs = queryString(
      buildRankingCentrosQuery(
        {
          startDate: "2025-07-01",
          endDate: "2026-06-30",
          costCenter: "0101",
        },
        10,
      ),
    );

    expect(qs).not.toContain("cost_center");
  });
});
