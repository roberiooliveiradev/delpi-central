import { describe, expect, it } from "vitest";

import {
  pessoalApprovalsHref,
  pessoalReviewDetailHref,
  resolveAppRoute,
  resolvePersonnelPlanId,
  routeHref,
} from "./routing";

describe("routing pessoal workflow", () => {
  it("resolve fila e detalhe", () => {
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/pessoal/aprovacoes"),
    ).toBe("pessoal-approvals");
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/pessoal/aprovacoes/plan-1"),
    ).toBe("pessoal-approval-detail");
    expect(resolvePersonnelPlanId("/apps/planejamento-orcamentario/pessoal/aprovacoes/plan-1")).toBe(
      "plan-1",
    );
  });

  it("hrefs", () => {
    expect(routeHref("pessoal-approvals")).toBe(
      "/apps/planejamento-orcamentario/pessoal/aprovacoes",
    );
    expect(pessoalApprovalsHref()).toBe(
      "/apps/planejamento-orcamentario/pessoal/aprovacoes",
    );
    expect(pessoalReviewDetailHref("abc")).toBe(
      "/apps/planejamento-orcamentario/pessoal/aprovacoes/abc",
    );
  });

  it("detalhe não aparece como rota de menu implícita no resolve de /pessoal", () => {
    expect(resolveAppRoute("/apps/planejamento-orcamentario/pessoal")).toBe("pessoal");
  });
});
