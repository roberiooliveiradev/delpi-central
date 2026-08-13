import { describe, expect, it } from "vitest";

import {
  buildOverviewClosingRateSeriesPayload,
  buildOverviewFunnelPayload,
  buildOverviewRolSeriesPayload,
} from "./overviewExportBuilders";

describe("overviewExportBuilders", () => {
  it("monta payload ROL com séries SC/ES", () => {
    const payload = buildOverviewRolSeriesPayload([
      {
        periodo: "01/08",
        sort_key: "2026-08-01",
        start_date: "2026-08-01",
        end_date: "2026-08-01",
        rol_matrix: 100,
        rol_branch: 50,
      },
    ]);
    expect(payload.title).toBe("Evolução do ROL (R$)");
    expect(payload.columns[1]?.label).toBe("ROL Santa Catarina");
    expect(payload.columns[2]?.label).toBe("ROL Espírito Santo");
    expect(payload.rows).toHaveLength(1);
  });

  it("inclui colunas do ano anterior quando solicitado", () => {
    const payload = buildOverviewRolSeriesPayload(
      [
        {
          periodo: "01/08",
          sort_key: "2026-08-01",
          start_date: "2026-08-01",
          end_date: "2026-08-01",
          rol_matrix: 100,
          rol_branch: 50,
          rol_matrix_prior: 80,
          rol_branch_prior: 40,
        },
      ],
      { includePriorYear: true },
    );
    expect(payload.columns).toHaveLength(5);
    expect(payload.rows[0]?.rolMatrixPrior).toBeTruthy();
  });

  it("inclui colunas prior no export da série de conversão", () => {
    const payload = buildOverviewClosingRateSeriesPayload(
      [
        {
          periodo: "01/08",
          sort_key: "2026-08-01",
          start_date: "2026-08-01",
          end_date: "2026-08-01",
          conversion_filial_01: 30,
          conversion_filial_02: 20,
          qtd_won_01: 3,
          qtd_proposals_01: 10,
          qtd_won_02: 2,
          qtd_proposals_02: 10,
          conversion_filial_01_prior: 25,
          conversion_filial_02_prior: 15,
        },
      ],
      { includePriorYear: true },
    );
    expect(payload.columns.some((c) => c.key === "conversion01Prior")).toBe(true);
    expect(payload.rows[0]?.conversion01Prior).toContain("%");
  });

  it("monta payload do funil", () => {
    const payload = buildOverviewFunnelPayload({
      qtd_proposals: 9,
      qtd_won: 3,
      sales_conversion_rate_pct: 33.33,
    });
    expect(payload.title).toBe("Funil de conversão");
    expect(payload.rows[0]?.valor).toBe("9");
    expect(payload.rows[1]?.valor).toBe("3");
  });
});
