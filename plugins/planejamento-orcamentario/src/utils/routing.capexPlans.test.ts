import { describe, expect, it } from "vitest";
import {
  capexApprovalsHref,
  capexReviewDetailHref,
  resolveAppRoute,
  resolveCapexPlanId,
} from "./routing";

describe("routing CAPEX workflow", () => {
  it("resolve fila e detalhe de aprovação", () => {
    expect(resolveAppRoute("/apps/planejamento-orcamentario/capex/aprovacoes")).toBe(
      "capex-approvals",
    );
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/capex/aprovacoes/plan-1"),
    ).toBe("capex-approval-detail");
    expect(
      resolveCapexPlanId("/apps/planejamento-orcamentario/capex/aprovacoes/plan-1"),
    ).toBe("plan-1");
    expect(capexApprovalsHref()).toBe("/apps/planejamento-orcamentario/capex/aprovacoes");
    expect(capexReviewDetailHref("abc")).toBe(
      "/apps/planejamento-orcamentario/capex/aprovacoes/abc",
    );
  });
});
