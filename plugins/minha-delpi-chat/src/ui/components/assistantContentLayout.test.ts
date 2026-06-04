import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./assistantContentSegments";
import {
  orderVisualSegments,
  resolveAssistantContentLayout,
} from "./assistantContentLayout";
import { filterSegmentsByVisualKind } from "./assistantContentVisualFormats";
import type { AssistantContentSegment } from "./assistantContentTypes";

describe("assistantContentLayout", () => {
  it("empilha visuais quando layoutMode é stack na API", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90260114/analyser",
          presentationDecision: {
            layoutMode: "stack",
            visualOrder: ["table", "tree", "chart"],
            availableViews: ["text", "table", "tree", "chart"],
          },
          presentation: { type: "tree", title: "Estrutura", root: { label: "PA", children: [] } },
          tablePresentation: {
            type: "table",
            title: "Produto",
            columns: [{ key: "campo", label: "Campo" }],
            rows: [{ campo: "Código", valor: "90260114" }],
          },
          chartPresentation: {
            type: "chart",
            chartType: "donut",
            title: "Composição",
            labels: ["PI (2)"],
            datasets: [{ label: "Itens", data: [2] }],
          },
          textPresentation: {
            type: "markdown",
            markdown: "Visão do produto com destaques.",
          },
        },
      },
    ];

    expect(resolveAssistantContentLayout("", toolCalls)).toBe("stack");

    const segments = buildAssistantContentSegments("", toolCalls);
    const kinds = segments.map((segment) => segment.kind);

    expect(kinds).toContain("markdown");
    expect(kinds).toContain("table");
    expect(kinds).toContain("tree");
    expect(kinds).toContain("chart");

    const tableView = filterSegmentsByVisualKind(segments, "table").map((item) => item.kind);

    expect(tableView).toContain("table");
    expect(tableView).not.toContain("tree");
  });

  it("ordena segmentos conforme visualOrder", () => {
    const visuals: AssistantContentSegment[] = [
      { kind: "chart", presentation: { type: "chart", chartType: "bar", title: "C", data: [] } },
      { kind: "table", presentation: { type: "table", title: "T", columns: [], rows: [] } },
      { kind: "tree", presentation: { type: "tree", title: "A", root: { label: "r", children: [] } } },
    ];

    const ordered = orderVisualSegments(visuals, ["table", "tree", "chart"]);

    expect(ordered.map((item) => item.kind)).toEqual(["table", "tree", "chart"]);
  });
});
