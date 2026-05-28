import { describe, expect, it } from "vitest";

import {
  getAvailableFormatsFromToolCalls,
  resolveRichTextContent,
  shouldSuppressMarkdownForPresentation,
  tablePresentationToMarkdown,
  type PresentationPair,
} from "./chatPresentation";

describe("shouldSuppressMarkdownForPresentation", () => {
  const toolCallsWithText = [
    {
      metadata: {
        availableFormats: ["text", "table", "chart"],
        textPresentation: {
          type: "markdown",
          title: "Indicador",
          markdown: "### Indicador\n\nLinha resumo.",
        },
        presentation: { type: "chart", title: "Indicador" },
        tablePresentation: { type: "table", title: "Indicador" },
      },
    },
  ];

  it("suprime markdown tabular quando há texto exibível no painel", () => {
    const pair: PresentationPair = {
      primary: { type: "chart", title: "Indicador" },
      table: { type: "table", title: "Indicador" },
    };

    expect(
      shouldSuppressMarkdownForPresentation(
        "| A | B |\n|---|---|\n| 1 | 2 |",
        pair,
        toolCallsWithText,
      ),
    ).toBe(true);
  });

  it("não suprime quando aba texto ficaria vazia", () => {
    const pair: PresentationPair = {
      primary: { type: "chart", title: "Indicador" },
      table: {
        type: "table",
        title: "Estoque",
        columns: [{ key: "a", label: "A" }],
        rows: [{ a: "1" }],
      },
    };

    expect(
      shouldSuppressMarkdownForPresentation("", pair, [
        { metadata: { availableFormats: ["text", "chart", "table"] } },
      ]),
    ).toBe(false);
  });

  it("mantém texto curto sem apresentação rica", () => {
    const pair: PresentationPair = {
      primary: { type: "chart", title: "Indicador" },
      table: null,
    };

    expect(
      shouldSuppressMarkdownForPresentation("Consulta concluída.", pair),
    ).toBe(false);
  });
});

describe("resolveRichTextContent", () => {
  it("prioriza conteúdo da mensagem e cai para textPresentation", () => {
    expect(resolveRichTextContent("Resposta curta", [])).toBe("Resposta curta");

    expect(
      resolveRichTextContent("", [
        {
          metadata: {
            textPresentation: {
              type: "markdown",
              title: "Estoque",
              markdown: "### Estoque\n\n10 unidades.",
            },
          },
        },
      ]),
    ).toBe("### Estoque\n\n10 unidades.");
  });

  it("gera markdown a partir da tabela quando não há texto", () => {
    const markdown = resolveRichTextContent("", [
      {
        metadata: {
          presentation: { type: "chart", title: "Estoque", chartType: "bar", data: [] },
          tablePresentation: {
            type: "table",
            title: "Estoque",
            columns: [{ key: "qtd", label: "Qtd" }],
            rows: [{ qtd: 10 }],
          },
        },
      },
    ]);

    expect(markdown).toContain("### Estoque");
    expect(markdown).toContain("| Qtd |");
    expect(markdown).toContain("| 10 |");
  });
});

describe("tablePresentationToMarkdown", () => {
  it("monta tabela markdown", () => {
    const markdown = tablePresentationToMarkdown({
      type: "table",
      title: "Produtos",
      columns: [
        { key: "code", label: "Código" },
        { key: "qty", label: "Qtd" },
      ],
      rows: [{ code: "100", qty: 2 }],
    });

    expect(markdown).toContain("### Produtos");
    expect(markdown).toContain("| Código | Qtd |");
    expect(markdown).toContain("| 100 | 2 |");
  });
});

describe("getAvailableFormatsFromToolCalls", () => {
  it("lê availableFormats do metadata", () => {
    expect(
      getAvailableFormatsFromToolCalls([
        { metadata: { availableFormats: ["text", "table", "chart"] } },
      ]),
    ).toEqual(["text", "table", "chart"]);
  });
});
