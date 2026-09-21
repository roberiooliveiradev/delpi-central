import { describe, expect, it } from "vitest";

import { dashboardRequestKey, isDashboardRefreshing, shouldCommitDashboardRequest } from "./dashboardRequest";

describe("dashboardRequest", () => {
  const base = {
    params: { competencia_inicio: "2026-08-01", competencia_fim: "2026-08-13", view: "consolidated" },
    siParams: { start_date: "2026-08-01", end_date: "2026-08-13" },
    granularity: "month",
    reloadNonce: 0,
  };

  it("muda a chave quando o período muda", () => {
    const month = dashboardRequestKey(base);
    const today = dashboardRequestKey({
      ...base,
      params: { ...base.params, competencia_inicio: "2026-08-13", competencia_fim: "2026-08-13" },
    });
    expect(today).not.toBe(month);
  });

  it("manual refresh muda a chave sem alterar filtros", () => {
    expect(dashboardRequestKey({ ...base, reloadNonce: 1 })).not.toBe(dashboardRequestKey(base));
  });

  it("sinaliza refresh antes da resposta, sem apagar a primeira leitura", () => {
    const month = dashboardRequestKey(base);
    const today = dashboardRequestKey({
      ...base,
      params: { ...base.params, competencia_inicio: "2026-08-13" },
    });
    expect(isDashboardRefreshing(false, null, month)).toBe(false);
    expect(isDashboardRefreshing(true, month, month)).toBe(false);
    expect(isDashboardRefreshing(true, month, today)).toBe(true);
  });
  it("só aplica a resposta do recorte mais novo", () => {
    const older = dashboardRequestKey(base);
    const newer = dashboardRequestKey({ ...base, reloadNonce: 1 });
    expect(shouldCommitDashboardRequest(newer, newer)).toBe(true);
    expect(shouldCommitDashboardRequest(older, newer)).toBe(false);
  });
});
