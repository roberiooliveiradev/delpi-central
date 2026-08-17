import { describe, expect, it } from "vitest";
import {
  exerciseMonthOptions,
  formatMoneyBr,
  investmentAccentTone,
  investmentCompletenessPercent,
  investmentSituation,
  isVersionConflictError,
  isWizardStepComplete,
  missingFieldLabel,
  monthValueToRequiredDate,
  normalizeMoneyInput,
  originLabel,
  priorityLabel,
  priorityTone,
  requiredDateMonthLabel,
  requiredDateToMonthValue,
  wizardProgressPercent,
  wizardStepBlockingMessage,
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
    expect(priorityLabel("2")).toBe("Alta");
    expect(priorityLabel("3")).toBe("Média");
    expect(priorityLabel("4")).toBe("Baixa");
    expect(priorityLabel("1")).toBe("Alta");
    expect(originLabel("imported")).toBe("Importado");
    expect(missingFieldLabel("required_date")).toMatch(/mês necessário|recebimento/i);
  });

  it("estima conclusão e situação da lista", () => {
    expect(investmentCompletenessPercent({ is_complete: true, missing_fields: [] })).toBe(100);
    expect(
      investmentCompletenessPercent({
        is_complete: false,
        missing_fields: ["category_id"],
      }),
    ).toBe(86);
    expect(
      investmentSituation({ is_complete: true, status: "draft", missing_fields: [] }).label,
    ).toBe("Pronto para revisão");
    expect(
      investmentSituation(
        { is_complete: true, status: "draft", missing_fields: [] },
        { planStatus: "submitted" },
      ).label,
    ).toBe("Aguardando decisão");
    expect(
      investmentSituation(
        {
          is_complete: true,
          status: "draft",
          missing_fields: [],
          review_status: "approved",
        },
        { planStatus: "submitted" },
      ).label,
    ).toBe("Aprovado");
    expect(
      investmentSituation(
        { is_complete: true, status: "draft", missing_fields: [] },
        { planStatus: "approved" },
      ).label,
    ).toBe("Aprovado");
    expect(
      investmentSituation(
        { is_complete: true, status: "draft", missing_fields: [] },
        { planStatus: "rejected" },
      ).label,
    ).toBe("Reprovado");
    expect(
      investmentSituation(
        { is_complete: true, status: "draft", missing_fields: [] },
        { planStatus: "changes_requested" },
      ).label,
    ).toBe("Ajustes solicitados");
    expect(
      investmentSituation({
        is_complete: false,
        status: "draft",
        missing_fields: ["category_id"],
      }).label,
    ).toMatch(/falta detalhar categoria/i);
    expect(priorityTone("2")).toBe("high");
    expect(investmentAccentTone("cat-1")).toMatch(/blue|orange|teal|violet/);
  });

  it("converte mês do exercício para data canônica", () => {
    expect(exerciseMonthOptions(2027)[0]).toEqual({
      value: "2027-01",
      label: "Janeiro de 2027",
    });
    expect(exerciseMonthOptions(2027)[1].label).toBe("Fevereiro de 2027");
    expect(requiredDateToMonthValue("2027-06-15")).toBe("2027-06");
    expect(monthValueToRequiredDate("2027-06")).toBe("2027-06-01");
    expect(requiredDateMonthLabel("2027-06-01")).toBe("Junho de 2027");
  });

  it("valida etapas do wizard de cadastro", () => {
    expect(wizardProgressPercent(0)).toBe(20);
    expect(wizardProgressPercent(4)).toBe(100);
    expect(
      wizardStepBlockingMessage(0, {
        cost_center_id: "205",
        category_id: "",
        description: "",
        estimated_amount: "",
        required_date: "",
        priority: "",
        origin: "",
      }),
    ).toMatch(/categoria/i);
    expect(
      isWizardStepComplete(
        1,
        {
          cost_center_id: "205",
          category_id: "c1",
          description: "Notebooks",
          estimated_amount: "",
          required_date: "",
          priority: "",
          origin: "",
        },
      ),
    ).toBe(true);
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
