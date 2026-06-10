import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./assistantContentSegments";
import {
  isNativeSingleViewSelection,
  orderVisualSegments,
  resolveAssistantContentLayout,
  resolveStackLayoutOrderFromToolCalls,
  shouldShowAllVisualSegments,
} from "./assistantContentLayout";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { fixtureToolCalls } from "./testFixtures";

describe("assistantContentLayout", () => {
  it("empilha visuais quando layoutMode é stack na API", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90260114/analyser",
          presentationDecision: {
            layoutMode: "stack",
            selected: "tree",
            visualOrder: ["text", "table", "tree", "chart"],
            availableViews: ["text", "table", "tree", "chart"],
          },
          presentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "90260114", label: "PA", children: [] },
          },
          tablePresentations: [
            {
              type: "table",
              title: "Roteiro de produção — 90260114",
              columns: [{ key: "product_code", label: "Produto" }],
              rows: [{ product_code: "90260114" }],
            },
            {
              type: "table",
              title: "Produto 90260114",
              columns: [{ key: "campo", label: "Campo" }],
              rows: [{ campo: "Código", valor: "90260114" }],
            },
          ],
          chartPresentation: {
            type: "chart",
            chartType: "donut",
            title: "Composição",
            data: [{ tipo: "PI", qtd: 2 }],
          },
          textPresentation: {
            type: "markdown",
            markdown: "Visão do produto com destaques.",
          },
        },
      },
    ]);

    expect(resolveAssistantContentLayout("", toolCalls)).toBe("stack");
    expect(resolveStackLayoutOrderFromToolCalls(toolCalls)).toEqual([
      "text",
      "table",
      "tree",
      "chart",
    ]);

    const segments = buildAssistantContentSegments("", toolCalls);
    const kinds = segments.map((segment) => segment.kind);
    const firstTableIndex = kinds.indexOf("table");
    const firstTreeIndex = kinds.indexOf("tree");
    const lastMarkdownBeforeTables = kinds
      .slice(0, firstTableIndex)
      .lastIndexOf("markdown");

    expect(kinds).toContain("markdown");
    expect(kinds).toContain("table");
    expect(kinds).toContain("tree");
    expect(kinds).toContain("chart");
    expect(firstTableIndex).toBeGreaterThanOrEqual(0);
    expect(firstTreeIndex).toBeGreaterThan(firstTableIndex);
    expect(lastMarkdownBeforeTables).toBeLessThanOrEqual(firstTableIndex);
    expect(shouldShowAllVisualSegments(toolCalls)).toBe(true);
  });

  it("ordena segmentos conforme visualOrder", () => {
    const visuals: AssistantContentSegment[] = [
      { kind: "chart", presentation: { type: "chart", chartType: "bar", title: "C", data: [] } },
      { kind: "table", presentation: { type: "table", title: "T", columns: [], rows: [] } },
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "A",
          root: { id: "r", label: "r", children: [] },
        },
      },
    ];

    const ordered = orderVisualSegments(visuals, ["table", "tree", "chart"]);

    expect(ordered.map((item) => item.kind)).toEqual(["table", "tree", "chart"]);
  });

  it("detecta visão nativa single quando selected=table", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            selected: "table",
            layoutMode: "single",
            visualOrder: ["table"],
          },
        },
      },
    ] as const;

    expect(isNativeSingleViewSelection(toolCalls)).toEqual({
      active: true,
      kind: "table",
    });
  });

  it("usa explicitSessionFormat=table quando selected=text (text-first stale)", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          explicitSessionFormat: "table",
          preferredFormat: "table",
          presentationDecision: {
            selected: "text",
            layoutMode: "single",
            visualOrder: ["text", "table"],
          },
          presentation: {
            type: "table",
            title: "Estoque do produto",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01" }],
          },
        },
      },
    ] as const;

    expect(isNativeSingleViewSelection(toolCalls)).toEqual({
      active: true,
      kind: "table",
    });

    const segments = buildAssistantContentSegments("Estoque do produto", [...toolCalls]);

    expect(segments.some((segment) => segment.kind === "table")).toBe(true);
    expect(segments.some((segment) => segment.kind === "markdown" && segment.markdown.includes("Stock:"))).toBe(
      false,
    );
  });

  it("usa explicitSessionFormat=tree quando selected=text (text-first stale)", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          explicitSessionFormat: "tree",
          preferredFormat: "tree",
          presentationDecision: {
            selected: "text",
            layoutMode: "single",
            visualOrder: ["text", "tree"],
          },
          presentation: {
            type: "tree",
            title: "Estoque do produto",
            root: { id: "10080022", label: "10080022", children: [] },
          },
        },
      },
    ] as const;

    expect(isNativeSingleViewSelection(toolCalls)).toEqual({
      active: true,
      kind: "tree",
    });

    const segments = buildAssistantContentSegments("Estoque do produto", [...toolCalls]);

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
  });
});
