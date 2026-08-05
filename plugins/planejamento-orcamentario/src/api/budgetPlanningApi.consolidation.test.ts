import { describe, expect, it, vi } from "vitest";

import { buildCapexConsolidationQuery } from "../api/budgetPlanningApi";
import { HttpRequestError } from "./httpClient";

describe("buildCapexConsolidationQuery", () => {
  it("serializa filtros ativos", () => {
    const qs = buildCapexConsolidationQuery({
      exercise_id: "ex-1",
      unit_id: "01",
      priority: "2",
      required_date_from: "2027-01-01",
    });
    expect(qs).toContain("exercise_id=ex-1");
    expect(qs).toContain("unit_id=01");
    expect(qs).toContain("priority=2");
    expect(qs).toContain("required_date_from=2027-01-01");
  });
});

describe("downloadAuthenticatedBinary error codes", () => {
  it("propaga código HTTP no HttpRequestError", async () => {
    const { downloadAuthenticatedBinary } = await import("./httpClient");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({
          message: "Moedas distintas",
          error: { code: "budget_capex_consolidation_currency_conflict" },
        }),
      }),
    );
    await expect(downloadAuthenticatedBinary("/capex/consolidation/export.xlsx")).rejects.toEqual(
      expect.objectContaining({
        status: 422,
        code: "budget_capex_consolidation_currency_conflict",
      } satisfies Partial<HttpRequestError>),
    );
    vi.unstubAllGlobals();
  });
});
