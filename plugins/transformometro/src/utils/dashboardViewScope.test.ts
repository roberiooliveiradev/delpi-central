import { describe, expect, it } from "vitest";

import { buildDashboardQueryParams, resolveDashboardViewMode } from "./dashboardViewScope";

describe("dashboardViewScope", () => {
  it("consolidado omite unidade e departamento", () => {
    expect(resolveDashboardViewMode({ filialIds: [], setorIds: [] })).toBe("consolidated");
    expect(
      buildDashboardQueryParams({
        dataInicial: "2026-09-01",
        dataFinal: "2026-09-21",
        filialIds: [],
        setorIds: [],
      }),
    ).toEqual({
      competencia_inicio: "2026-09-01",
      competencia_fim: "2026-09-21",
      view: "consolidated",
    });
  });

  it("unidade envia só filial_id", () => {
    expect(resolveDashboardViewMode({ filialIds: ["01"], setorIds: [] })).toBe("filial");
    const params = buildDashboardQueryParams({
      dataInicial: "2026-09-01",
      dataFinal: "2026-09-21",
      filialIds: ["01"],
      setorIds: [],
    });
    expect(params).toMatchObject({
      view: "filial",
      filial_id: "01",
    });
    expect(params.setor_id).toBeUndefined();
  });

  it("departamento envia filial e setor", () => {
    expect(resolveDashboardViewMode({ filialIds: ["01"], setorIds: ["dep-1"] })).toBe("department");
    expect(
      buildDashboardQueryParams({
        filialIds: ["01"],
        setorIds: ["dep-1"],
      }),
    ).toEqual({
      view: "department",
      filial_id: "01",
      setor_id: "dep-1",
    });
  });
});
