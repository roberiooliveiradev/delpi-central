import { describe, expect, it } from "vitest";

import { collectVisualSegments } from "./visualSegmentCollector";
import { fixtureToolCalls } from "../../message/testFixtures";

describe("collectVisualSegments", () => {
  it("não monta dashboard quando a API omitiu dashboardPresentation", () => {
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
            renderHints: {
              suppressedKinds: ["dashboard"],
            },
          },
          treePresentation: {
            type: "tree",
            title: "Estrutura fabril",
            root: { id: "90262404", label: "90262404", children: [] },
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toContain("tree");
    expect(kinds).not.toContain("dashboard");
  });

  it("mantém dashboard quando a API envia dashboardPresentation", () => {
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

  it("ignora visuais latentes quando renderPlan v1 não os inclui", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "tree", slot: "tailVisuals", source: "treePresentation" },
            ],
          },
          treePresentation: {
            type: "tree",
            title: "Estrutura fabril",
            root: { id: "90262404", label: "90262404", children: [] },
          },
          dashboardPresentation: {
            type: "dashboard",
            title: "Painel latente",
            panels: [],
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toEqual(["tree"]);
  });
});
