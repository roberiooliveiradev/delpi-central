import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./assistantContentSegments";
import {
  filterSegmentsByVisualKind,
  resolveAvailableVisualFormatOptions,
  resolveDefaultVisualKind,
} from "./assistantContentVisualFormats";
import { fixtureToolCalls } from "./testFixtures";

describe("assistantContentVisualFormats", () => {
  const toolCalls = fixtureToolCalls([
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
          root: { id: "PA", label: "PA", children: [] },
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
          data: [{ tipo: "PI", qtd: 1 }],
        },
        textPresentation: {
          type: "markdown",
          markdown: "Resumo narrativo.",
        },
      },
    },
  ]);

  it("lista opções de troca para cada visual disponível", () => {
    const segments = buildAssistantContentSegments("", toolCalls);
    const options = resolveAvailableVisualFormatOptions(segments, toolCalls);

    expect(options.map((item) => item.kind)).toEqual(["text", "table", "tree", "chart"]);
    expect(resolveDefaultVisualKind(toolCalls, options)).toBe("text");
    expect(options.map((item) => item.label)).toEqual([
      "Texto",
      "Tabela",
      "Árvore",
      "Gráfico",
    ]);
  });

  it("mantém narrativa e tabelas complementares na visão árvore", () => {
    const analyserLike = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            layoutMode: "stack",
            availableViews: ["text", "table", "tree"],
            visualOrder: ["text", "table", "tree"],
            selected: "tree",
          },
          presentation: {
            type: "tree",
            title: "Estrutura do produto 90260149",
            root: { id: "90260149", label: "90260149", children: [] },
          },
          tablePresentations: [
            {
              type: "table",
              title: "Roteiro de produção — 90260149",
              columns: [{ key: "product_code", label: "Produto" }],
              rows: [{ product_code: "90260149" }],
            },
            {
              type: "table",
              title: "Produto 90260149",
              columns: [{ key: "campo", label: "Campo" }],
              rows: [{ campo: "Código", valor: "90260149" }],
            },
          ],
          textPresentation: {
            type: "markdown",
            markdown:
              "### Informações completas do produto 90260149\n\n**Destaques**\n\n- Item.\n\n**Pontos de atenção encontrados na API:**\n\n1. Bloqueio.",
          },
        },
      },
    ]);
    const segments = buildAssistantContentSegments("", analyserLike);
    const filteredTree = filterSegmentsByVisualKind(segments, "tree");
    const kinds = filteredTree.map((segment) => segment.kind);

    expect(kinds).toEqual(["stackSection", "tree"]);
    expect(
      segments.some(
        (segment) =>
          segment.kind === "markdown" && segment.markdown.includes("**Pontos de atenção"),
      ),
    ).toBe(true);
  });

  it("filtra segmentos pelo formato ativo", () => {
    const segments = buildAssistantContentSegments("", toolCalls);
    const filteredTable = filterSegmentsByVisualKind(segments, "table");
    const tableKinds = filteredTable.map((segment) => segment.kind);

    expect(tableKinds).not.toContain("markdown");
    expect(tableKinds).toContain("table");
    expect(tableKinds).not.toContain("tree");
    expect(tableKinds).not.toContain("chart");

    const filteredText = filterSegmentsByVisualKind(segments, "text");
    const textKinds = filteredText.map((segment) => segment.kind);

    expect(textKinds).toContain("markdown");
    expect(textKinds).not.toContain("table");
    expect(textKinds).not.toContain("tree");
    expect(textKinds).not.toContain("chart");
  });

  it("usa formato selecionado pela API como padrão", () => {
    const withTree = fixtureToolCalls([
      {
        ...toolCalls[0],
        metadata: {
          ...toolCalls[0].metadata,
          presentationDecision: {
            ...(toolCalls[0].metadata?.presentationDecision ?? {}),
            selected: "tree",
          },
          preferredFormat: "tree",
        },
      },
    ]);
    const segments = buildAssistantContentSegments("", withTree);
    const options = resolveAvailableVisualFormatOptions(segments, withTree);

    expect(resolveDefaultVisualKind(withTree, options)).toBe("tree");
  });

  it("prioriza árvore em rotas de estrutura quando não há formato explícito", () => {
    const analyserCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90260144/analyser",
          presentationDecision: {
            selected: "tree",
            availableViews: ["text", "table", "tree"],
            visualOrder: ["text", "tree", "table"],
            layoutMode: "stack",
          },
          preferredFormat: "tree",
          presentation: {
            type: "tree",
            title: "Estrutura do produto 90260144",
            root: { id: "90260144", label: "90260144", children: [] },
          },
          tablePresentation: {
            type: "table",
            title: "Produto 90260144",
            columns: [{ key: "campo", label: "Campo" }],
            rows: [{ campo: "Código", valor: "90260144" }],
          },
          textPresentation: { type: "markdown", markdown: "Resumo." },
        },
      },
    ]);
    const segments = buildAssistantContentSegments("", analyserCalls);
    const options = resolveAvailableVisualFormatOptions(segments, analyserCalls);

    expect(resolveDefaultVisualKind(analyserCalls, options)).toBe("tree");
  });

  it("respeita texto quando a API seleciona narrativa", () => {
    const analyserCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90260144/analyser",
          presentationDecision: {
            selected: "text",
            availableViews: ["text", "table", "tree"],
            visualOrder: ["text", "tree", "table"],
            layoutMode: "stack",
          },
          preferredFormat: "text",
          presentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "90260144", label: "90260144", children: [] },
          },
          tablePresentation: {
            type: "table",
            title: "Produto",
            columns: [{ key: "campo", label: "Campo" }],
            rows: [{ campo: "Código", valor: "90260144" }],
          },
          textPresentation: { type: "markdown", markdown: "Resumo." },
        },
      },
    ]);
    const segments = buildAssistantContentSegments("", analyserCalls);
    const options = resolveAvailableVisualFormatOptions(segments, analyserCalls);

    expect(resolveDefaultVisualKind(analyserCalls, options)).toBe("text");
  });
});
