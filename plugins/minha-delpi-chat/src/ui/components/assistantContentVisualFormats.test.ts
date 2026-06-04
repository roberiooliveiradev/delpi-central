import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./assistantContentSegments";
import {
  filterSegmentsByVisualKind,
  resolveAvailableVisualFormatOptions,
  resolveDefaultVisualKind,
} from "./assistantContentVisualFormats";

describe("assistantContentVisualFormats", () => {
  const toolCalls = [
    {
      name: "execute_external_action",
      metadata: {
        presentationDecision: {
          selected: "text",
          availableViews: ["text", "table", "tree", "chart"],
          visualOrder: ["table", "tree", "chart"],
          layoutMode: "stack",
        },
        preferredFormat: "text",
        presentation: {
          type: "tree",
          title: "Estrutura",
          root: { label: "PA", children: [] },
        },
        tablePresentation: {
          type: "table",
          title: "Cadastro",
          columns: [{ key: "campo", label: "Campo" }],
          rows: [{ campo: "Código", valor: "1" }],
        },
        chartPresentation: {
          type: "chart",
          chartType: "donut",
          title: "Composição",
          labels: ["PI"],
          datasets: [{ label: "Itens", data: [1] }],
        },
        textPresentation: {
          type: "markdown",
          markdown: "Resumo narrativo.",
        },
      },
    },
  ];

  it("lista opções de troca para cada visual disponível", () => {
    const segments = buildAssistantContentSegments("", toolCalls);
    const options = resolveAvailableVisualFormatOptions(segments, toolCalls);

    expect(options.map((item) => item.kind)).toEqual(["table", "tree", "chart"]);
    expect(options.map((item) => item.label)).toEqual(["Tabela", "Árvore", "Gráfico"]);
  });

  it("filtra segmentos pelo formato ativo", () => {
    const segments = buildAssistantContentSegments("", toolCalls);
    const filtered = filterSegmentsByVisualKind(segments, "table");
    const kinds = filtered.map((segment) => segment.kind);

    expect(kinds).toContain("markdown");
    expect(kinds).toContain("table");
    expect(kinds).not.toContain("tree");
    expect(kinds).not.toContain("chart");
  });

  it("usa formato selecionado pela API como padrão", () => {
    const withTree = [
      {
        ...toolCalls[0],
        metadata: {
          ...toolCalls[0].metadata,
          presentationDecision: {
            ...toolCalls[0].metadata.presentationDecision,
            selected: "tree",
          },
          preferredFormat: "tree",
        },
      },
    ];
    const segments = buildAssistantContentSegments("", withTree);
    const options = resolveAvailableVisualFormatOptions(segments, withTree);

    expect(resolveDefaultVisualKind(withTree, options)).toBe("tree");
  });
});
