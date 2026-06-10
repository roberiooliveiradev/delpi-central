import { describe, expect, it } from "vitest";

import {
  resolveAssistantDisplayContent,
  resolveAssistantPresentationTitle,
  resolveAssistantRenderableMarkdown,
  resolveAssistantStreamingProseState,
  shouldBypassIncrementalTextReveal,
  shouldRenderPresentationHeading,
  stripLeadingMarkdownTitleSafely,
  toolCallsForDrawingAnalysisDisplay,
} from "./assistantProseRendering";

describe("assistantProseRendering", () => {
  it("remove marcadores section:* do conteúdo exibido do assistente", () => {
    const markdown =
      "### Escopo\n\n<!-- section:scope -->\n\n10070012 — CABO PP.";

    expect(
      resolveAssistantDisplayContent(markdown, [], undefined),
    ).toBe("### Escopo\n\n10070012 — CABO PP.");
  });

  it("remove marcadores section:* do markdown renderizável", () => {
    const markdown =
      "### Escopo\n\n<!-- section:scope -->\n\n10070012 — CABO PP.\n\n<!-- section:highlights -->";

    expect(resolveAssistantRenderableMarkdown(markdown, [])).toBe(
      "### Escopo\n\n10070012 — CABO PP.",
    );
  });

  it("não trata saudação com negrito como título de apresentação", () => {
    const greeting = "Olá! Sou o **Agente Minha DELPI**. O que vamos consultar?";

    expect(resolveAssistantPresentationTitle(greeting, [])).toBe("");
    expect(shouldRenderPresentationHeading(greeting)).toBe(false);
    expect(resolveAssistantRenderableMarkdown(greeting, [])).toBe(greeting);
  });

  it("não remove o corpo quando título coincide com a mensagem inteira", () => {
    const body = "Olá! Sou o **Agente Minha DELPI**.";

    expect(stripLeadingMarkdownTitleSafely(body, body)).toBe(body);
  });

  it("modo texto usa markdown completo do metadata, incluindo bloco de árvore", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            selected: "text",
            layoutMode: "single",
          },
          textPresentation: {
            type: "markdown",
            title: "Estrutura do produto 90260149",
            markdown:
              "### Estrutura do produto 90260149\n\nProduto **90260149**.\n\n**Composição**\n\n```\n90260149 PA 1 MI — RAIZ\n└── C1 PI 1 UN — COMP\n```",
          },
        },
      },
    ] as const;

    const rendered = resolveAssistantRenderableMarkdown("", [...toolCalls]);

    expect(rendered).toContain("**Composição**");
    expect(rendered).toContain("└── C1 PI 1 UN — COMP");
  });

  it("remove apenas cabeçalho real distinto do corpo", () => {
    const body = "### Estoque\n\n| Filial | Qtd |\n| --- | --- |";

    expect(stripLeadingMarkdownTitleSafely(body, "Estoque")).toBe(
      "| Filial | Qtd |\n| --- | --- |",
    );
  });

  it("desliga reveal incremental quando há markdown parcial", () => {
    expect(shouldBypassIncrementalTextReveal("Olá! Sou o **Agente")).toBe(true);
    expect(shouldBypassIncrementalTextReveal("Texto simples.")).toBe(false);
  });

  it("streaming com markdown usa ChatMarkdown imediatamente", () => {
    const answer = "Olá! Sou o **Agente Minha DELPI**.";

    expect(
      resolveAssistantStreamingProseState({
        answer,
        revealedAnswer: "Olá! Sou o *",
        suppressRichPresentation: false,
        isGenerating: true,
        isPlayback: false,
      }),
    ).toEqual({
      markdownContent: answer,
      enableCharReveal: false,
      captionUsesMarkdown: true,
    });
  });

  it("streaming sem markdown mantém reveal incremental", () => {
    expect(
      resolveAssistantStreamingProseState({
        answer: "Consulta concluída.",
        revealedAnswer: "Consulta con",
        suppressRichPresentation: false,
        isGenerating: true,
        isPlayback: false,
      }),
    ).toEqual({
      markdownContent: "Consulta con",
      enableCharReveal: true,
      captionUsesMarkdown: false,
    });
  });

  it("prioriza markdown do relatório de desenho no corpo da mensagem", () => {
    const report = "## Relatório de Análise de Desenho DELPI\n\n| Item | Status |";
    const metadata = {
      drawingAnalysisMode: true,
      drawingAnalysisExport: { filename: "relatorio.md", mimeType: "text/markdown", markdown: report },
    };

    expect(
      resolveAssistantDisplayContent(
        "Informações completas do produto 90260140",
        [
          {
            name: "execute_external_action",
            metadata: {
              path: "/products/90260140/analyser",
              textPresentation: { markdown: "### Ficha analyser" },
            },
          },
        ],
        metadata,
      ),
    ).toBe(report);
  });

  it("remove apresentação rica do analyser em turno de relatório de desenho", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90260140/analyser",
          presentation: { type: "tree", title: "Estrutura", root: { id: "90260140" } },
          humanizedSummary: { titulo: "Ficha", linhas: [] },
        },
      },
    ];
    const stripped = toolCallsForDrawingAnalysisDisplay(toolCalls, {
      drawingAnalysisMode: true,
      drawingAnalysisExport: {
        filename: "relatorio.md",
        mimeType: "text/markdown",
        markdown: "## Relatório",
      },
    });

    expect(stripped[0].metadata?.presentation).toBeUndefined();
    expect(stripped[0].metadata?.path).toContain("/analyser");
  });
});
