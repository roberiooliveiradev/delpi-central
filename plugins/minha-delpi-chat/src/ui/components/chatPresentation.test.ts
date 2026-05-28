import { describe, expect, it } from "vitest";

import {
  getAvailableFormatsFromToolCalls,
  resolveRichTextContent,
  shouldSuppressMarkdownForPresentation,
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

  it("suprime markdown tabular quando há gráfico e aba texto", () => {
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

  it("mantém texto curto sem apresentação rica nem aba texto", () => {
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
