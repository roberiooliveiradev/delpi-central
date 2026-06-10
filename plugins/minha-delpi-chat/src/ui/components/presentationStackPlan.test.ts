import { describe, expect, it } from "vitest";

import { bucketTableSegmentsByRole } from "./assistantContentInterleave";
import {
  getStackPresentationPlanFromToolCalls,
  inferTableRoleFromTitle,
  resolveTableRole,
} from "./presentationStackPlan";
import { fixtureToolCalls } from "./testFixtures";

describe("presentationStackPlan", () => {
  it("infere papéis de tabela por título", () => {
    expect(inferTableRoleFromTitle("Produto 90260149")).toBe("profile");
    expect(inferTableRoleFromTitle("Roteiro de produção — 1")).toBe("guide");
    expect(inferTableRoleFromTitle("Estoque por filial")).toBe("stock");
  });

  it("prefere role da API quando presente", () => {
    expect(resolveTableRole("Estoque por filial", { role: "list" })).toBe("list");
    expect(resolveTableRole("Produto 90260149", { role: "profile" })).toBe("profile");
    expect(resolveTableRole("Título genérico", { role: "invalid" })).toBe("other");
  });

  it("bucket ignora inferência quando role vem no metadata", () => {
    const buckets = bucketTableSegmentsByRole([
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Estoque por filial",
          role: "list",
          columns: [],
          rows: [],
        },
      },
    ]);

    expect(buckets.list).toHaveLength(1);
    expect(buckets.stock).toHaveLength(0);
  });

  it("lê plano de estoque só do stackPresentationPlan (sem fallback por path)", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90260149/stock",
          stackPresentationPlan: {
            tableRoleOrder: ["profile", "stock", "list"],
            tailVisualOrder: ["chart", "table"],
          },
        },
      },
    ]);

    const plan = getStackPresentationPlanFromToolCalls(toolCalls);

    expect(plan.tableRoleOrder).toEqual(["profile", "stock", "list"]);
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
