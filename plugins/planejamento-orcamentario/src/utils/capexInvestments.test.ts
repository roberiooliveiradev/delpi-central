import { describe, expect, it } from "vitest";
import {
  formatMoneyBr,
  isVersionConflictError,
  missingFieldLabel,
  normalizeMoneyInput,
  originLabel,
  priorityLabel,
} from "./capexInvestments";
import { HttpRequestError } from "../api/httpClient";
import {
  capexInvestmentHref,
  capexNewInvestmentHref,
  resolveAppRoute,
  resolveCapexInvestmentId,
} from "./routing";

describe("capexInvestments utils", () => {
  it("normaliza valor monetário sem float", () => {
    expect(normalizeMoneyInput("1.500,50")).toBe("1500.50");
    expect(normalizeMoneyInput("10")).toBe("10");
    expect(formatMoneyBr("1500.5")).toBe("R$ 1.500,50");
  });

  it("labels de prioridade e origem", () => {
    expect(priorityLabel("2")).toMatch(/Maior necessidade/);
    expect(originLabel("imported")).toBe("Importado");
    expect(missingFieldLabel("required_date")).toMatch(/recebimento/i);
  });

  it("detecta conflito de versão", () => {
    expect(
      isVersionConflictError(
        new HttpRequestError("[budget_capex_version_conflict] x", 409),
      ),
    ).toBe(true);
    expect(isVersionConflictError(new HttpRequestError("other", 409))).toBe(false);
  });
});

describe("rotas CAPEX investimentos", () => {
  it("resolve novo e edição", () => {
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/capex/investimentos/novo"),
    ).toBe("capex-investment-new");
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/capex/investimentos/abc-1"),
    ).toBe("capex-investment-edit");
    expect(
      resolveCapexInvestmentId("/apps/planejamento-orcamentario/capex/investimentos/abc-1"),
    ).toBe("abc-1");
    expect(capexNewInvestmentHref({ costCenterId: "205" })).toContain("cost_center_id=205");
    expect(
      capexNewInvestmentHref({ costCenterId: "205", unitId: "01" }),
    ).toContain("unit_id=01");
    expect(capexInvestmentHref("inv-1")).toContain("/capex/investimentos/inv-1");
  });
});
