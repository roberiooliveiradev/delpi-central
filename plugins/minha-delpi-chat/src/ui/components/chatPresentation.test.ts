import { describe, expect, it } from "vitest";

import {
  buildAssistantCopyText,
  getAvailableFormatsFromToolCalls,
  getPresentationTitle,
  isShortPresentationCaption,
  resolveRichTextBody,
  resolveRichTextContent,
  shouldShowRichPresentation,
  shouldSuppressMarkdownForPresentation,
  tablePresentationToMarkdown,
  type PresentationPair,
} from "./chatPresentation";

const stockToolCalls = [
  {
    metadata: {
      availableFormats: ["text", "table", "chart"],
      presentation: {
        type: "chart",
        title: "Estoque por filial/armazém",
        chartType: "bar",
        data: [],
      },
      tablePresentation: {
        type: "table",
        title: "Estoque do produto",
        columns: [
          { key: "branch", label: "Filial" },
          { key: "qty", label: "Qtd. atual" },
        ],
        rows: [
          { branch: "01", qty: 4 },
          { branch: "02", qty: 2 },
        ],
      },
    },
  },
];

describe("resolveRichTextBody", () => {
  it("gera tabela markdown quando a mensagem é só o título compactado", () => {
    const body = resolveRichTextBody("Estoque por filial/armazém", stockToolCalls);

    expect(body).toContain("| Filial | Qtd. atual |");
    expect(body).toContain("| 01 | 4 |");
    expect(body).not.toContain("### Estoque por filial");
  });

  it("usa título do gráfico no cabeçalho compartilhado", () => {
    expect(getPresentationTitle("Estoque por filial/armazém", stockToolCalls)).toBe(
      "Estoque por filial/armazém",
    );
  });
});

describe("isShortPresentationCaption", () => {
  it("detecta legenda curta do presenter", () => {
    expect(
      isShortPresentationCaption("Estoque por filial/armazém", stockToolCalls),
    ).toBe(true);
  });

  it("não trata pergunta do usuário como legenda só por ter toolCalls", () => {
    expect(
      isShortPresentationCaption("estoque do produto 10080015", stockToolCalls),
    ).toBe(false);
  });
});

describe("buildAssistantCopyText", () => {
  it("inclui título e tabela markdown na cópia", () => {
    const text = buildAssistantCopyText(
      "Estoque por filial/armazém",
      stockToolCalls,
    );

    expect(text).toContain("Estoque por filial/armazém");
    expect(text).toContain("| Filial | Qtd. atual |");
    expect(text).toContain("| 01 | 4 |");
  });
});

describe("shouldShowRichPresentation", () => {
  it("não exibe painel rico quando só há textPresentation duplicando o markdown", () => {
    const profileAnswer =
      "**Seu perfil na Minha DELPI:**\n\n- **Nome:** Robério\n- **Email:** rob@delpi.com";
    const toolCalls = [
      {
        metadata: {
          textPresentation: {
            type: "markdown",
            title: "Seu perfil na Minha DELPI",
            markdown: profileAnswer,
          },
        },
      },
    ];

    expect(shouldShowRichPresentation(profileAnswer, toolCalls)).toBe(false);
  });

  it("exibe painel rico para tabela/gráfico", () => {
    expect(shouldShowRichPresentation("Estoque", stockToolCalls)).toBe(true);
  });
});

describe("shouldSuppressMarkdownForPresentation", () => {
  it("suprime legenda curta quando o painel exibe tabela em markdown", () => {
    const pair: PresentationPair = {
      primary: { type: "chart", title: "Estoque por filial/armazém" },
      table: stockToolCalls[0].metadata.tablePresentation as PresentationPair["table"],
    };

    expect(
      shouldSuppressMarkdownForPresentation(
        "Estoque por filial/armazém",
        pair,
        stockToolCalls,
      ),
    ).toBe(true);
  });

  it("mantém texto curto sem apresentação rica", () => {
    expect(
      shouldSuppressMarkdownForPresentation("Consulta concluída.", {
        primary: null,
        table: null,
      }),
    ).toBe(false);
  });
});

describe("tablePresentationToMarkdown", () => {
  it("omite título quando solicitado", () => {
    const markdown = tablePresentationToMarkdown(
      {
        type: "table",
        title: "Estoque",
        columns: [{ key: "a", label: "A" }],
        rows: [{ a: "1" }],
      },
      { includeTitle: false },
    );

    expect(markdown).not.toContain("###");
    expect(markdown).toContain("| A |");
  });
});

describe("resolveRichTextContent", () => {
  it("combina título e corpo para compatibilidade", () => {
    const markdown = resolveRichTextContent("Estoque por filial/armazém", stockToolCalls);

    expect(markdown).toContain("### Estoque por filial/armazém");
    expect(markdown).toContain("| Filial |");
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
