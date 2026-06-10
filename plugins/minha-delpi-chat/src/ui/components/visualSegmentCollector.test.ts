import { describe, expect, it } from "vitest";

import { collectVisualSegments } from "./visualSegmentCollector";
import { fixtureToolCalls } from "./testFixtures";

describe("collectVisualSegments", () => {
  it("omite dashboard em summary_then_evidence automático", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["tree", "chart"],
          },
          treePresentation: {
            type: "tree",
            title: "Estrutura fabril",
            root: { id: "90262404", label: "90262404", children: [] },
          },
          dashboardPresentation: {
            type: "dashboard",
            title: "Painel fabril",
            panels: [],
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toContain("tree");
    expect(kinds).not.toContain("dashboard");
  });

  it("mantém dashboard quando explicitSessionFormat é dashboard", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          explicitSessionFormat: "dashboard",
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["dashboard"],
          },
          dashboardPresentation: {
            type: "dashboard",
            title: "Painel fabril",
            panels: [],
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toContain("dashboard");
  });
});
