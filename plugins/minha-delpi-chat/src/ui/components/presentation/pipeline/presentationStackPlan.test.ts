import { describe, expect, it } from "vitest";

import { bucketTableSegmentsByRole } from "../../message/assistantContentInterleave";
import {
  getStackPresentationPlanFromToolCalls,
  inferTableRoleFromTitle,
  planUsesSummaryThenEvidence,
  resolveTableRole,
} from "./presentationStackPlan";
import { fixtureToolCalls } from "../../message/testFixtures";

describe("presentationStackPlan", () => {
  it("fallback legacy retorna other quando role ausente na API", () => {
    expect(inferTableRoleFromTitle("Produto 90260149")).toBe("other");
    expect(inferTableRoleFromTitle("Roteiro de produção — 1")).toBe("other");
    expect(inferTableRoleFromTitle("Estoque por filial")).toBe("other");
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

  it("lê presentationMode do presentationDecision quando o stackPlan não traz o campo", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: { presentationMode: "summary_then_evidence" },
        },
      },
    ]);

    expect(planUsesSummaryThenEvidence(getStackPresentationPlanFromToolCalls(toolCalls))).toBe(
      true,
    );
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
