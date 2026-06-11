import { describe, expect, it } from "vitest";

import type { AssistantContentSegment } from "./assistantContentTypes";
import { buildCanonicalStackSegments } from "./presentationStackBlueprint";
import { buildSegmentsFromRenderPlan } from "./renderPlanSegmentBuilder";

function parseMarkdown(prose: string): AssistantContentSegment[] {
  return [{ kind: "markdown", markdown: prose }];
}

describe("renderPlanSegmentBuilder", () => {
  it("monta stack evidence-first a partir do renderPlan da API", () => {
    const commentary = "### Status fabril\n\nSituação consolidada.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura fabril",
          root: { id: "90262404", label: "90262404", children: [] },
        },
      },
      {
        kind: "chart",
        presentation: {
          type: "chart",
          chartType: "bar",
          title: "Saldo MP",
          data: [{ label: "MP", value: 1 }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["tree", "chart"],
            narrativeOrder: ["lead", "operationalTables", "tailVisuals"],
            renderHints: { textRenderMode: "compact", tailVisualPolicy: "allowlist" },
          },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "tree", slot: "tailVisuals", source: "treePresentation" },
              { kind: "chart", slot: "tailVisuals", source: "chartPresentation" },
            ],
          },
        },
      },
    ] as never;

    const segments = buildSegmentsFromRenderPlan(
      commentary,
      visuals,
      parseMarkdown,
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    const kinds = (segments ?? []).map((segment) => segment.kind);

    expect(kinds).toContain("markdown");
    expect(kinds).toContain("tree");
    expect(kinds).toContain("chart");
    expect(kinds).not.toContain("dashboard");
    expect(kinds).not.toContain("stackSection");
  });

  it("buildCanonicalStackSegments prioriza renderPlan quando presente", () => {
    const commentary = "### Status fabril\n\nSituação consolidada.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura fabril",
          root: { id: "90262404", label: "90262404", children: [] },
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["tree"],
            narrativeOrder: ["lead", "tailVisuals"],
          },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "tree", slot: "tailVisuals", source: "treePresentation" },
            ],
          },
        },
      },
    ] as never;

    const segments = buildCanonicalStackSegments(
      commentary,
      visuals,
      parseMarkdown,
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
    expect(segments.some((segment) => segment.kind === "stackSection")).toBe(false);
  });

  it("não usa blueprint legado quando renderPlan v1 omite dashboard", () => {
    const commentary = "### Status fabril\n\nSituação consolidada.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura fabril",
          root: { id: "90262404", label: "90262404", children: [] },
        },
      },
      {
        kind: "dashboard",
        presentation: {
          type: "dashboard",
          title: "Painel fabril",
          panels: [],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["tree"],
            narrativeOrder: ["lead", "tailVisuals"],
          },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "tree", slot: "tailVisuals", source: "treePresentation" },
            ],
          },
        },
      },
    ] as never;

    const segments = buildCanonicalStackSegments(
      commentary,
      visuals,
      parseMarkdown,
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
    expect(segments.some((segment) => segment.kind === "dashboard")).toBe(false);
  });
});
