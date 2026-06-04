import { describe, expect, it } from "vitest";

import { getStackPresentationPlanFromToolCalls, inferTableRoleFromTitle } from "./presentationStackPlan";
import { fixtureToolCalls } from "./testFixtures";

describe("presentationStackPlan", () => {
  it("infere papéis de tabela por título", () => {
    expect(inferTableRoleFromTitle("Produto 90260149")).toBe("profile");
    expect(inferTableRoleFromTitle("Roteiro de produção — 1")).toBe("guide");
    expect(inferTableRoleFromTitle("Estoque por filial")).toBe("stock");
  });

  it("lê plano do analyser no metadata", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/1/analyser",
          stackPresentationPlan: {
            profileFirst: true,
            highlightsAfterProfile: true,
            attentionLast: true,
            tableRoleOrder: ["profile", "guide", "inspection", "other"],
            tailVisualOrder: ["tree", "chart"],
            narrativeOrder: [
              "lead",
              "profileTables",
              "highlights",
              "operationalTables",
              "tailVisuals",
              "attention",
            ],
          },
        },
      },
    ]);

    const plan = getStackPresentationPlanFromToolCalls(toolCalls);

    expect(plan.tableRoleOrder[0]).toBe("profile");
    expect(plan.narrativeOrder.at(-1)).toBe("attention");
  });
});
