import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./assistantContentSegments";
import {
  filterSegmentsByVisualKind,
  resolveAvailableVisualFormatOptions,
  resolveDefaultVisualKind,
  resolveInitialToolbarKind,
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
          path: "/products/90260149/analyser",
          stackPresentationPlan: {
            presentationProfile: "product_analyser",
            humanizedSections: true,
            sectionVisibility: {
              scope: true,
              profile: true,
              highlights: true,
              guide: true,
              inspection: false,
              structure: true,
              attention: true,
            },
            narrativeOrder: [
              "lead",
              "profileTables",
              "highlights",
              "operationalTables",
              "tailVisuals",
              "attention",
            ],
            tableRoleOrder: ["profile", "guide", "inspection"],
            tailVisualOrder: ["tree"],
          },
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
        (segment) => segment.kind === "markdown" && segment.markdown.includes("1. Bloqueio"),
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
    expect(textKinds).toContain("table");
    expect(textKinds).toContain("tree");
    expect(textKinds).toContain("chart");
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

  it("no stack analyser sem escolha explícita, inicia em Completo", () => {
    const analyserCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/10070012/analyser",
          presentationDecision: {
            selected: "text",
            availableViews: ["text", "table", "tree"],
            visualOrder: ["text", "table", "tree"],
            layoutMode: "stack",
            reason: "consulta completa do produto — visão integrada (stack)",
          },
          preferredFormat: "text",
          presentation: {
            type: "tree",
            title: "Estrutura do produto 10070012",
            root: { id: "10070012", label: "10070012", children: [] },
          },
          tablePresentation: {
            type: "table",
            title: "Produto 10070012",
            columns: [{ key: "campo", label: "Campo" }],
            rows: [{ campo: "Código", valor: "10070012" }],
          },
          textPresentation: {
            type: "markdown",
            markdown: "### Informações completas do produto 10070012",
          },
        },
      },
    ]);
    const segments = buildAssistantContentSegments("", analyserCalls);
    const options = resolveAvailableVisualFormatOptions(segments, analyserCalls);

    expect(resolveInitialToolbarKind(analyserCalls, options)).toBeNull();
  });

  it("no stack com KPI, inicia em texto quando o formato solicitado é texto", () => {
    const kpiCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            selected: "text",
            availableViews: ["text", "kpi", "table", "chart"],
            visualOrder: ["text", "kpi", "table", "chart"],
            layoutMode: "stack",
            reason: "formato solicitado pelo usuário",
          },
          preferredFormat: "text",
          explicitSessionFormat: "text",
          presentation: {
            type: "kpi",
            title: "Indicadores de RH",
            cards: [{ label: "PDIs ativos", value: 29 }],
          },
          textPresentation: {
            type: "markdown",
            markdown: "### Indicadores de RH\n\n**PDIs ativos:** 29",
          },
        },
      },
    ]);
    const segments = buildAssistantContentSegments("", kpiCalls);
    const options = resolveAvailableVisualFormatOptions(segments, kpiCalls);

    expect(resolveInitialToolbarKind(kpiCalls, options)).toBe("text");

    const visible = filterSegmentsByVisualKind(segments, "text");

    expect(visible.some((segment) => segment.kind === "kpi")).toBe(true);
    expect(visible.some((segment) => segment.kind === "markdown")).toBe(true);
  });

  it("no modo texto do analyser mantém narrativa intercalada com visuais", () => {
    const analyserLike = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            layoutMode: "stack",
            availableViews: ["text", "table", "tree"],
            visualOrder: ["text", "table", "tree"],
            selected: "text",
          },
          path: "/products/90260149/analyser",
          presentation: {
            type: "tree",
            title: "Estrutura do produto 90260149",
            root: { id: "90260149", label: "90260149", children: [] },
          },
          tablePresentation: {
            type: "table",
            title: "Produto 90260149",
            columns: [{ key: "campo", label: "Campo" }],
            rows: [{ campo: "Código", valor: "90260149" }],
          },
          textPresentation: {
            type: "markdown",
            markdown: "### Informações completas\n\n**Destaques**\n\n- Item.",
          },
          stackPresentationPlan: {
            presentationProfile: "product_analyser",
            humanizedSections: true,
            sectionVisibility: {
              scope: true,
              profile: true,
              highlights: true,
              structure: true,
              attention: false,
            },
            narrativeOrder: ["lead", "profileTables", "highlights", "tailVisuals"],
            tableRoleOrder: ["profile"],
            tailVisualOrder: ["tree"],
          },
        },
      },
    ]);
    const segments = buildAssistantContentSegments("", analyserLike);
    const visible = filterSegmentsByVisualKind(segments, "text");
    const kinds = visible.map((segment) => segment.kind);

    expect(kinds).toContain("markdown");
    expect(kinds).toContain("table");
    expect(kinds).toContain("tree");
    expect(kinds).toContain("stackSection");
  });

  it("inicia em KPI quando a decisão da API seleciona kpi", () => {
    const kpiCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            selected: "kpi",
            availableViews: ["text", "kpi", "chart", "table"],
            visualOrder: ["text", "kpi", "chart", "table"],
            layoutMode: "single",
          },
          presentation: {
            type: "kpi",
            title: "Taxa de Conversão de Vendas",
            cards: [{ label: "Atual", value: "82,5%" }],
          },
          textPresentation: {
            type: "markdown",
            markdown:
              "### Taxa de Conversão de Vendas\n\n<!-- section:scope -->\n\nIndicador com 3 métricas.",
          },
        },
      },
    ]);
    const segments = buildAssistantContentSegments("", kpiCalls);
    const options = resolveAvailableVisualFormatOptions(segments, kpiCalls);

    expect(resolveInitialToolbarKind(kpiCalls, options)).toBe("kpi");
    expect(resolveDefaultVisualKind(kpiCalls, options)).toBe("kpi");
  });
});
