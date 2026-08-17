import { describe, expect, it } from "vitest";

import type { CapexPlan, PersonnelPlan } from "../types/budgetPlanning";
import {
  amountFromPlanStatusGroups,
  applyConsolidationAmountsToPortfolio,
  approvalPlanStatusLabel,
  groupApprovalPortfolioByUnit,
  mergeApprovalPortfolio,
  portfolioPendingCounts,
  portfolioToChartItems,
  type EnrichedCapexPlan,
} from "./approvalPortfolio";

function capex(
  partial: Partial<EnrichedCapexPlan> & {
    unit_id: string;
    cost_center_id: string;
    status: string;
  },
): EnrichedCapexPlan {
  return {
    id: partial.id ?? `c-${partial.cost_center_id}`,
    exercise_id: "ex-1",
    version: 1,
    total_amount: partial.total_amount ?? "1000",
    investment_count: partial.investment_count ?? 1,
    ...partial,
  } as EnrichedCapexPlan;
}

function personnel(
  partial: Partial<PersonnelPlan> & {
    unit_id: string;
    cost_center_id: string;
    status: string;
  },
): PersonnelPlan {
  return {
    id: partial.id ?? `p-${partial.cost_center_id}`,
    exercise_id: "ex-1",
    version: 1,
    position_count: 1,
    lines: [],
    totals: { headcount_dec_2027: 5, ...(partial.totals ?? {}) },
    ...partial,
  } as PersonnelPlan;
}

describe("mergeApprovalPortfolio", () => {
  it("une CAPEX e Pessoal do mesmo CC e ordena por urgência", () => {
    const merged = mergeApprovalPortfolio(
      [
        capex({
          unit_id: "02",
          cost_center_id: "0205",
          status: "submitted",
          total_amount: "50000",
        }),
        capex({
          unit_id: "02",
          cost_center_id: "0203",
          status: "submitted",
          total_amount: "1000",
        }),
      ],
      [
        personnel({
          unit_id: "02",
          cost_center_id: "0205",
          status: "submitted",
        }),
      ],
    );
    expect(merged).toHaveLength(2);
    expect(merged[0].cost_center_id).toBe("0205");
    expect(merged[0].capexPending).toBe(true);
    expect(merged[0].personnelPending).toBe(true);
    expect(merged[1].personnelPending).toBe(false);
  });

  it("propaga icon_key e nome do centro de custo do plano", () => {
    const merged = mergeApprovalPortfolio(
      [
        capex({
          unit_id: "02",
          cost_center_id: "0205",
          status: "submitted",
          cost_center_icon_key: "wrench",
          cost_center_name: "Manutenção",
          cost_center_owner_name: "Ana Silva",
        }),
      ],
      [],
    );
    expect(merged).toHaveLength(1);
    expect(merged[0].icon_key).toBe("wrench");
    expect(merged[0].cost_center_name).toBe("Manutenção");
    expect(merged[0].owner_name).toBe("Ana Silva");
  });

  it("inclui rascunhos como em andamento só com investimento e prioriza enviados", () => {
    const merged = mergeApprovalPortfolio(
      [
        capex({
          unit_id: "02",
          cost_center_id: "0201",
          status: "draft",
          total_amount: "8000",
          investment_count: 2,
        }),
        capex({
          unit_id: "02",
          cost_center_id: "0202",
          status: "submitted",
          total_amount: "3000",
        }),
      ],
      [],
    );
    expect(merged).toHaveLength(2);
    expect(merged[0].cost_center_id).toBe("0202");
    expect(merged[0].capexPending).toBe(true);
    expect(merged[1].cost_center_id).toBe("0201");
    expect(merged[1].capexInProgress).toBe(true);
    expect(merged[1].capexPending).toBe(false);
    expect(approvalPlanStatusLabel("draft")).toBe("Em andamento");
  });

  it("rascunho CAPEX sem investimento não conta como em andamento", () => {
    const merged = mergeApprovalPortfolio(
      [
        capex({
          unit_id: "02",
          cost_center_id: "0502",
          status: "draft",
          investment_count: 0,
        }),
      ],
      [
        personnel({
          unit_id: "02",
          cost_center_id: "0502",
          status: "draft",
          position_count: 0,
          totals: { headcount_dec_2027: 0 },
        }),
      ],
    );
    expect(merged).toHaveLength(1);
    expect(merged[0].capexInProgress).toBe(false);
    expect(merged[0].personnelInProgress).toBe(false);
  });

  it("agrupa centros por filial 01 e 02 com rótulos de cidade", () => {
    const merged = mergeApprovalPortfolio(
      [
        capex({
          unit_id: "02",
          cost_center_id: "0502",
          status: "draft",
          investment_count: 0,
        }),
        capex({
          unit_id: "01",
          cost_center_id: "0101",
          status: "submitted",
          total_amount: "1000",
        }),
      ],
      [],
    );
    const groups = groupApprovalPortfolioByUnit(merged);
    expect(groups.map((g) => g.unit_id)).toEqual(["01", "02"]);
    expect(groups[0].title).toContain("Jaraguá do Sul");
    expect(groups[1].title).toContain("Rio Bananal");
    expect(groups[0].items).toHaveLength(1);
    expect(groups[1].items).toHaveLength(1);
  });

  it("conta pendências e gera itens de gráfico", () => {
    const merged = mergeApprovalPortfolio(
      [
        capex({
          unit_id: "01",
          cost_center_id: "0101",
          status: "submitted",
          total_amount: "2000",
        }) as CapexPlan & EnrichedCapexPlan,
      ],
      [],
    );
    const counts = portfolioPendingCounts(merged);
    expect(counts.centersWithPending).toBe(1);
    expect(counts.capexPending).toBe(1);
    expect(counts.capexPendingAmount).toBe(2000);
    expect(counts.centersTracked).toBe(1);
    expect(portfolioToChartItems(merged)[0]?.code).toBe("0101");
  });

  it("aplica totais da consolidação e lê valor por status", () => {
    const merged = mergeApprovalPortfolio(
      [capex({ unit_id: "02", cost_center_id: "0203", status: "draft" })],
      [],
    );
    const withAmounts = applyConsolidationAmountsToPortfolio(merged, [
      {
        code: "0203",
        description: "Manutenção",
        investment_count: 2,
        total_amount: "122600",
        unit_id: "02",
        cost_center_id: "0203",
      },
    ]);
    expect(withAmounts[0].capexAmount).toBe(122600);
    expect(withAmounts[0].cost_center_name).toBe("Manutenção");
    expect(
      amountFromPlanStatusGroups(
        [
          { code: "draft", description: "Rascunho", investment_count: 1, total_amount: "5000" },
          {
            code: "submitted",
            description: "Enviado",
            investment_count: 1,
            total_amount: "122600",
          },
        ],
        "draft",
      ),
    ).toBe(5000);
  });

  it("não aplica total consolidado de outra filial com o mesmo código de CC", () => {
    const merged = mergeApprovalPortfolio(
      [
        capex({
          unit_id: "01",
          cost_center_id: "0203",
          status: "draft",
          investment_count: 1,
          total_amount: "8000",
        }),
      ],
      [],
    );
    const withAmounts = applyConsolidationAmountsToPortfolio(merged, [
      {
        code: "0203",
        description: "RH",
        investment_count: 5,
        total_amount: "130600",
        unit_id: "02",
        cost_center_id: "0203",
      },
      {
        code: "0203",
        description: "RH",
        investment_count: 1,
        total_amount: "8000",
        unit_id: "01",
        cost_center_id: "0203",
      },
    ]);
    expect(withAmounts[0].capexAmount).toBe(8000);
  });
});
