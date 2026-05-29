import { describe, expect, it } from "vitest";

import {
  buildAssistantCopyText,
  getAvailableFormatsFromToolCalls,
  getPresentationPairFromToolCalls,
  getPresentationTitle,
  isShortPresentationCaption,
  resolveRichTextBody,
  resolveCommentaryTextBody,
  resolvePresentationLayoutMode,
  resolveRichTextContent,
  shouldShowRichPresentation,
  shouldShowActionResults,
  shouldStackPresentationBlocks,
  shouldSuppressMarkdownForPresentation,
  stripRedundantStructureFromMarkdown,
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
      tree: null,
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

describe("tree presentation", () => {
  const analyserToolCalls = [
    {
      name: "execute_external_action",
      metadata: {
        availableFormats: ["text", "tree", "table"],
        preferredFormat: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura do produto 90260148",
          root: {
            id: "90260148",
            label: "90260148",
            badge: "PA",
            children: [
              {
                id: "50220013",
                label: "50220013",
                badge: "PI",
                children: [{ id: "10030015", label: "10030015", badge: "MP" }],
              },
            ],
          },
        },
        tablePresentation: {
          type: "table",
          title: "Componentes da estrutura 90260148",
          columns: [{ key: "component_code", label: "Componente" }],
          rows: [{ component_code: "10030015" }],
        },
        textPresentation: {
          type: "markdown",
          title: "Informações completas do produto 90260148",
          markdown:
            "### Informações completas do produto 90260148\n\nProduto **90260148**: CHICOTE.\n\n**Estrutura do produto 90260148**\n\n| Código | Descrição |\n| --- | --- |\n| 50220013 | PI |\n\n**Insights**\n\n- Custo padrão vigente: R$ 272,80.",
        },
      },
    },
  ];

  const structureToolCalls = [
    {
      name: "execute_external_action",
      metadata: {
        availableFormats: ["text", "tree", "table"],
        preferredFormat: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura do produto 90260148",
          root: {
            id: "90260148",
            label: "90260148",
            badge: "PA",
            children: [
              {
                id: "50220013",
                label: "50220013",
                badge: "PI",
                children: [{ id: "10030015", label: "10030015", badge: "MP" }],
              },
            ],
          },
        },
        tablePresentation: {
          type: "table",
          title: "Componentes da estrutura 90260148",
          columns: [{ key: "component_code", label: "Componente" }],
          rows: [{ component_code: "10030015" }],
        },
      },
    },
  ];

  it("empilha blocos complementares do analyser", () => {
    const pair = getPresentationPairFromToolCalls(analyserToolCalls);

    expect(resolvePresentationLayoutMode(analyserToolCalls, pair)).toBe("commentary-visual");
    expect(getPresentationTitle("", analyserToolCalls)).toBe(
      "Informações completas do produto 90260148",
    );

    const commentary = resolveCommentaryTextBody("", analyserToolCalls, pair);

    expect(commentary).toContain("Produto **90260148**");
    expect(commentary).toContain("Insights");
    expect(commentary).not.toContain("50220013 | PI");
    expect(commentary).toContain("estrutura");
  });

  it("remove markdown duplicado da estrutura quando há árvore", () => {
    const markdown =
      "Perfil do produto.\n\n**Estrutura do produto 90260148**\n\n| Código | Descrição |\n| --- | --- |\n| 50220013 | PI |\n\n**Insights**\n\n- Item 1.";

    expect(stripRedundantStructureFromMarkdown(markdown)).toBe(
      "Perfil do produto.\n\n**Insights**\n\n- Item 1.",
    );
  });

  it("suprime legenda curta duplicada quando a resposta é empilhada", () => {
    const pair = getPresentationPairFromToolCalls(analyserToolCalls);

    expect(
      shouldSuppressMarkdownForPresentation(
        "Componentes da estrutura 90260148",
        pair,
        analyserToolCalls,
      ),
    ).toBe(true);
  });

  it("resolve par primary/tree/table para estrutura", () => {
    const pair = getPresentationPairFromToolCalls(structureToolCalls);

    expect(pair.primary?.type).toBe("tree");
    expect(pair.tree?.type).toBe("tree");
    expect(pair.table?.type).toBe("table");
    expect(getAvailableFormatsFromToolCalls(structureToolCalls)).toEqual([
      "text",
      "tree",
      "table",
    ]);
    expect(shouldShowRichPresentation("", structureToolCalls)).toBe(true);
  });
});

describe("shouldShowActionResults", () => {
  it("oculta JSON bruto quando há apresentação rica", () => {
    expect(
      shouldShowActionResults("Estoque por filial/armazém", stockToolCalls),
    ).toBe(false);
  });

  it("oculta JSON bruto quando há textPresentation humanizado", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          textPresentation: {
            type: "markdown",
            markdown: "### Faturamento\n\n**Valor faturado:** R$ 21.024,26",
          },
        },
      },
    ];

    expect(shouldShowActionResults("", toolCalls)).toBe(false);
  });
});
