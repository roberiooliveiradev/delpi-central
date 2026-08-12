import { describe, expect, it } from "vitest";

import { buildOverviewFunnelPayload, buildOverviewRolSeriesPayload } from "./overviewExportBuilders";

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
