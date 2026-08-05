import { describe, expect, it } from "vitest";

import {
  draftToFilters,
  emptyConsolidationDraft,
  isCurrencyConflictError,
  mapCapexConsolidationError,
  topGroupItemsByAmount,
} from "./capexConsolidation";
import { HttpRequestError } from "../api/httpClient";
import { resolveAppRoute, routeHref } from "./routing";
import {
  hasCapexConsolidationViewAccess,
  hasCapexExportAccess,
} from "./permissions";

describe("capexConsolidation helpers", () => {
  it("converte draft em filtros omitindo vazios", () => {
    expect(
      draftToFilters({
        ...emptyConsolidationDraft,
        exercise_id: "ex-1",
        unit_id: "01",
        priority: "",
      }),
    ).toEqual({ exercise_id: "ex-1", unit_id: "01" });
  });

  it("mapeia conflito de moedas e 401/403", () => {
    const conflict = new HttpRequestError("x", 422, {
      code: "budget_capex_consolidation_currency_conflict",
    });
    expect(isCurrencyConflictError(conflict)).toBe(true);
    expect(mapCapexConsolidationError(conflict)).toMatch(/moedas diferentes/i);

    expect(mapCapexConsolidationError(new HttpRequestError("x", 401))).toMatch(/Sessão expirada/i);
    expect(mapCapexConsolidationError(new HttpRequestError("x", 403))).toMatch(/permissão/i);
    expect(mapCapexConsolidationError(new HttpRequestError("rede", 0))).toMatch(/rede/i);
  });

  it("ordena e limita maiores valores", () => {
    const top = topGroupItemsByAmount(
      [
        { code: "a", description: "A", investment_count: 1, total_amount: "10.00" },
        { code: "b", description: "B", investment_count: 1, total_amount: "90.00" },
        { code: "c", description: "C", investment_count: 1, total_amount: "40.00" },
      ],
      2,
    );
    expect(top.map((i) => i.code)).toEqual(["b", "c"]);
  });
});

describe("routing consolidação", () => {
  it("resolve rota e href", () => {
    expect(resolveAppRoute("/apps/planejamento-orcamentario/capex/consolidacao")).toBe(
      "capex-consolidation",
    );
    expect(routeHref("capex-consolidation")).toBe(
      "/apps/planejamento-orcamentario/capex/consolidacao",
    );
  });
});

describe("permissions consolidação", () => {
  it("exige consolidation.view ou admin; export separado", () => {
    expect(
      hasCapexConsolidationViewAccess({
        permissions: ["planejamento-orcamentario.capex.consolidation.view"],
      } as never),
    ).toBe(true);
    expect(
      hasCapexConsolidationViewAccess({
        permissions: ["planejamento-orcamentario.access"],
      } as never),
    ).toBe(false);
    expect(
      hasCapexExportAccess({
        permissions: ["planejamento-orcamentario.capex.export"],
      } as never),
    ).toBe(true);
    expect(
      hasCapexExportAccess({
        permissions: ["planejamento-orcamentario.capex.consolidation.view"],
      } as never),
    ).toBe(false);
  });
});
