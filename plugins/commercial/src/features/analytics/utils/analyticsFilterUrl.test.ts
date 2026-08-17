import { describe, expect, it } from "vitest";

import {
  buildAnalyticsFilterSearchParams,
  buildAnalyticsOpportunityBackSearch,
  readAnalyticsFilters,
  readAnalyticsOpportunitySearch,
} from "./analyticsFilterUrl";

describe("analyticsFilterUrl — busca de oportunidades", () => {
  it("hidrata search da URL com normalização", () => {
    expect(readAnalyticsOpportunitySearch("?search=%20ACME%20")).toBe("ACME");
    expect(readAnalyticsOpportunitySearch("?branch=01")).toBe("");
  });

  it("mantém search e filtros reconhecidos no retorno", () => {
    const back = buildAnalyticsOpportunityBackSearch(
      "?search=ACME&branch=01&customer_segment=weg&nao_permitido=x",
    );
    expect(back).toContain("search=ACME");
    expect(back).toContain("branch=01");
    expect(back).toContain("customer_segment=weg");
    expect(back).not.toContain("nao_permitido");
  });
});

describe("analyticsFilterUrl — sellerIds multi", () => {
  it("lê CSV de seller_id e serializa de volta", () => {
    const state = readAnalyticsFilters(
      "?start_date=2026-01-01&end_date=2026-01-31&seller_id=p1,p2",
    );
    expect(state.sellerIds).toEqual(["p1", "p2"]);
    expect(state.periodPreset).toBeNull();
    const params = buildAnalyticsFilterSearchParams(state);
    expect(params).toContain("seller_id=p1%2Cp2");
  });
});

describe("analyticsFilterUrl — period_preset", () => {
  it("persiste e lê period_preset na URL", () => {
    const state = readAnalyticsFilters(
      "?start_date=2026-08-17&end_date=2026-08-17&period_preset=this_week",
    );
    expect(state.periodPreset).toBe("this_week");
    const params = buildAnalyticsFilterSearchParams({
      ...state,
      periodPreset: "this_week",
    });
    expect(params).toContain("period_preset=this_week");
  });

  it("omite period_preset quando null ou custom", () => {
    const params = buildAnalyticsFilterSearchParams({
      dateStart: "2026-08-17",
      dateEnd: "2026-08-17",
      competence: "",
      branches: [],
      customerSegment: "",
      sellerIds: [],
      periodPreset: null,
    });
    expect(params).not.toContain("period_preset");
  });
});
