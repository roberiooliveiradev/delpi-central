import { describe, expect, it } from "vitest";

import {
  buildAssistantCopyText,
  getAvailableFormatsFromToolCalls,
  getPresentationPairFromToolCalls,
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

describe("multi-product presentation merge", () => {
  const multiStockToolCalls = [
    {
      name: "execute_external_action",
      metadata: {
        availableFormats: ["text", "table", "chart"],
        presentation: {
          type: "chart",
          title: "Estoque por filial/armazém",
          chartType: "bar",
          config: { xAxis: "name", yAxis: ["Qtd. atual"], legend: true },
          data: [{ name: "Fil.01/01", "Qtd. atual": 9024 }],
        },
        tablePresentation: {
          type: "table",
          title: "Estoque do produto",
          columns: [
            { key: "branch", label: "Filial" },
            { key: "product_code", label: "Produto" },
            { key: "current_quantity", label: "Qtd. atual" },
          ],
          rows: [{ branch: "01", product_code: "10080047", current_quantity: 9024 }],
        },
        textPresentation: {
          type: "markdown",
          markdown: "### Estoque do produto\n\nFilial 01: 9024",
        },
      },
    },
    {
      name: "execute_external_action",
      metadata: {
        availableFormats: ["text", "table", "chart"],
        presentation: {
          type: "chart",
          title: "Estoque por filial/armazém",
          chartType: "bar",
          config: { xAxis: "name", yAxis: ["Qtd. atual"], legend: true },
          data: [{ name: "Fil.02/99", "Qtd. atual": 115 }],
        },
        tablePresentation: {
          type: "table",
          title: "Estoque do produto",
          columns: [
            { key: "branch", label: "Filial" },
            { key: "product_code", label: "Produto" },
            { key: "current_quantity", label: "Qtd. atual" },
          ],
          rows: [{ branch: "02", product_code: "10080055", current_quantity: 115 }],
        },
        textPresentation: {
          type: "markdown",
          markdown: "### Estoque do produto\n\nFilial 02: 115",
        },
      },
    },
  ];

  it("mescla linhas de tabela de vários produtos", () => {
    const pair = getPresentationPairFromToolCalls(multiStockToolCalls);
    const table = pair.table;

    expect(table?.type).toBe("table");
    expect(table?.rows).toHaveLength(2);
    expect(table?.rows.map((row) => row.product_code)).toEqual([
      "10080047",
      "10080055",
    ]);

    const body = resolveRichTextBody("", multiStockToolCalls);

    expect(body).toContain("10080047");
    expect(body).toContain("10080055");
    expect(shouldShowRichPresentation("", multiStockToolCalls)).toBe(true);
  });

  it("mescla markdown textual de várias consultas", () => {
    const markdown = resolveRichTextContent("", multiStockToolCalls);

    expect(markdown).toContain("9024");
    expect(markdown).toContain("115");
  });
});
