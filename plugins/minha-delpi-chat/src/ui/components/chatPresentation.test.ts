import { describe, expect, it } from "vitest";

import type { ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";
import {
  buildAssistantCopyText,
  getAvailableFormatsFromToolCalls,
  getPresentationDecisionFromToolCalls,
  getPresentationInsightFromToolCalls,
  mapPresentationDecisionToViewFormat,
  getChartPresentationFromPair,
  getPresentationPairFromToolCalls,
  getPresentationTitle,
  isStructureLikeToolCalls,
  resolveDefaultRichViewMode,
  resolveRichFormatToggles,
  isShortPresentationCaption,
  resolveRichTextBody,
  resolveCommentaryTextBody,
  getPaginationStateFromToolCalls,
  stripCoverageNoticeFromMarkdown,
  resolvePresentationLayoutMode,
  resolveRichTextContent,
  shouldShowRichPresentation,
  shouldShowActionResults,
  shouldStackPresentationBlocks,
  shouldSuppressMarkdownForPresentation,
  stripRedundantInspectionDumpFromMarkdown,
  stripRedundantStructureFromMarkdown,
  tablePresentationToMarkdown,
  type PresentationPair,
} from "./chatPresentation";

/** Aceita literais de fixture e tipa como ChatToolCall[] para o compilador. */
function fixtureToolCalls(calls: unknown[]): ChatToolCall[] {
  return calls as ChatToolCall[];
}

const stockToolCalls = fixtureToolCalls([
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
]);

describe("resolveRichTextBody", () => {
  it("suprime legenda que repete só o título quando há painel rico", () => {
    const body = resolveRichTextBody("Estoque por filial/armazém", stockToolCalls);

    expect(body).toBe("");
    expect(body).not.toContain("| Filial | Qtd. atual |");
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
  it("inclui título e legenda na cópia quando o painel exibe tabela/gráfico", () => {
    const text = buildAssistantCopyText(
      "Estoque por filial/armazém",
      stockToolCalls,
    );

    expect(text).toContain("Estoque por filial/armazém");
    expect(text).not.toContain("| Filial | Qtd. atual |");
  });
});

describe("shouldShowRichPresentation", () => {
  it("não exibe painel rico quando só há textPresentation duplicando o markdown", () => {
    const profileAnswer =
      "**Seu perfil na Minha DELPI:**\n\n- **Nome:** Robério\n- **Email:** rob@delpi.com";
    const toolCalls = fixtureToolCalls([
      {
        metadata: {
          textPresentation: {
            type: "markdown",
            title: "Seu perfil na Minha DELPI",
            markdown: profileAnswer,
          },
        },
      },
    ]);

    expect(shouldShowRichPresentation(profileAnswer, toolCalls)).toBe(false);
  });

  it("exibe painel rico para tabela/gráfico", () => {
    expect(shouldShowRichPresentation("Estoque", stockToolCalls)).toBe(true);
  });
});

describe("shouldSuppressMarkdownForPresentation", () => {
  it("suprime legenda curta quando o painel exibe tabela em markdown", () => {
    const pair: PresentationPair = {
      primary: stockToolCalls[0]!.metadata!.presentation as ChatPresentation,
      table: stockToolCalls[0]!.metadata!.tablePresentation as PresentationPair["table"],
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
        tree: null,
      }),
    ).toBe(false);
  });

  it("suprime markdown duplicado com painel multi-formato (estoque em texto)", () => {
    const multiFormatCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          availableFormats: ["text", "table", "chart"],
          preferredFormat: "text",
          presentation: {
            type: "markdown",
            markdown: "### Estoque\n\nFilial 01, armazém 01: atual 160242.",
          },
          tablePresentation: {
            type: "table",
            title: "Estoque",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01" }],
          },
          chartPresentation: {
            type: "chart",
            title: "Estoque",
            chartType: "bar",
            config: { xAxis: "name", yAxis: ["Qtd. atual"], legend: true },
            data: [{ name: "Fil.01/01", "Qtd. atual": 160242 }],
          },
        },
      },
    ]);
    const pair = getPresentationPairFromToolCalls(multiFormatCalls);
    const longProse =
      "Filial 01, armazém 01: atual 160242, disponível 160242. " +
      "Filial 02, armazém 99: atual 8436, disponível -35883.";

    expect(
      shouldSuppressMarkdownForPresentation(longProse, pair, multiFormatCalls),
    ).toBe(true);
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
  it("retorna só o título quando o corpo repete a legenda do painel", () => {
    const markdown = resolveRichTextContent("Estoque por filial/armazém", stockToolCalls);

    expect(markdown).toBe("Estoque por filial/armazém");
    expect(markdown).not.toContain("| Filial |");
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

describe("isStructureLikeToolCalls", () => {
  it("detecta rotas de estrutura", () => {
    expect(
      isStructureLikeToolCalls(
        fixtureToolCalls([
          {
            metadata: { path: "/products/90260174/analyser" },
          },
        ]),
      ),
    ).toBe(true);
  });
});

describe("resolveRichFormatToggles", () => {
  it("expõe Texto, Árvore e Tabela e oculta gráfico quando há árvore", () => {
    expect(
      resolveRichFormatToggles({
        hasText: true,
        hasChart: true,
        hasTable: true,
        hasTree: true,
        isCommentaryVisual: false,
      }),
    ).toEqual({
      showText: true,
      showTree: true,
      showTable: true,
      showChart: false,
    });
  });

  it("mantém gráfico quando não há árvore", () => {
    expect(
      resolveRichFormatToggles({
        hasText: false,
        hasChart: true,
        hasTable: true,
        hasTree: false,
        isCommentaryVisual: false,
      }).showChart,
    ).toBe(true);
  });
});

describe("presentationDecision (Playbook 09)", () => {
  it("mapeia line_chart para modo gráfico", () => {
    expect(mapPresentationDecisionToViewFormat("line_chart")).toBe("chart");
    expect(mapPresentationDecisionToViewFormat("horizontal_bar")).toBe("chart");
    expect(mapPresentationDecisionToViewFormat("table")).toBe("table");
  });

  it("usa availableViews do metadata", () => {
    const formats = getAvailableFormatsFromToolCalls(
      fixtureToolCalls([
        {
          metadata: {
            presentationDecision: {
              selected: "line_chart",
              availableViews: ["line_chart", "table", "chart"],
            },
          },
        },
      ]),
    );

    expect(formats).toContain("chart");
    expect(formats).toContain("table");
  });

  it("inicia em gráfico quando decision pede line_chart", () => {
    const toolCalls = fixtureToolCalls([
      {
        metadata: {
          presentationDecision: {
            selected: "line_chart",
            reason: "dados temporais com valor numérico",
            availableViews: ["line_chart", "table"],
          },
          preferredFormat: "chart",
          presentation: {
            type: "chart",
            title: "Vendas",
            chartType: "line",
            data: [],
          },
          tablePresentation: {
            type: "table",
            title: "Tabela",
            columns: [{ key: "month", label: "Mês" }],
            rows: [{ month: "jan", value: 1 }],
          },
        },
      },
    ]);

    expect(
      resolveDefaultRichViewMode(toolCalls, {
        hasText: false,
        hasChart: true,
        hasTable: true,
        hasTree: false,
      }),
    ).toBe("chart");

    expect(getPresentationInsightFromToolCalls(toolCalls)).toBe(
      "dados temporais com valor numérico",
    );
  });
});

describe("resolveDefaultRichViewMode", () => {
  it("inicia em árvore quando há apresentação em árvore", () => {
    const toolCalls = fixtureToolCalls([
      {
        metadata: {
          path: "/products/1/analyser",
          preferredFormat: "table",
          presentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "1", label: "1" },
          },
          tablePresentation: {
            type: "table",
            title: "Tabela",
            columns: [{ key: "c", label: "C" }],
            rows: [{ c: "1" }],
          },
        },
      },
    ]);

    expect(
      resolveDefaultRichViewMode(toolCalls, {
        hasText: true,
        hasChart: false,
        hasTable: true,
        hasTree: true,
        commentaryVisual: true,
      }),
    ).toBe("tree");
  });
});

describe("getPresentationPairFromToolCalls", () => {
  it("prioriza árvore como primary em rotas de estrutura", () => {
    const pair = getPresentationPairFromToolCalls(
      fixtureToolCalls([
        {
          name: "execute_external_action",
          metadata: {
            path: "/products/90260174/analyser",
            presentation: {
              type: "tree",
              title: "Estrutura",
              root: { id: "90260174", label: "90260174" },
            },
            tablePresentation: {
              type: "table",
              title: "Componentes",
              columns: [{ key: "code", label: "Código" }],
              rows: [{ code: "10030015" }],
            },
          },
        },
      ]),
    );

    expect(pair.primary?.type).toBe("tree");
    expect(pair.table?.type).toBe("table");
  });
});

describe("getChartPresentationFromPair", () => {
  it("prioriza árvore no primary e ainda resolve gráfico complementar", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          presentation: { type: "tree", title: "Onde é usado", root: { id: "1", label: "1" } },
          chartPresentation: {
            type: "chart",
            title: "Extra",
            chartType: "bar",
            data: [{ name: "A", value: 1 }],
            config: { xAxis: "name", yAxis: ["value"] },
          },
        },
      },
    ]);
    const pair = getPresentationPairFromToolCalls(toolCalls);

    expect(pair.tree?.type).toBe("tree");
    expect(pair.primary?.type).toBe("tree");
    expect(getChartPresentationFromPair(pair, toolCalls)?.title).toBe("Extra");
  });
});

describe("multi-product presentation merge", () => {
  const multiStockToolCalls = fixtureToolCalls([
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
  ]);

  it("mescla linhas de tabela de vários produtos", () => {
    const pair = getPresentationPairFromToolCalls(multiStockToolCalls);
    const table = pair.table;

    expect(table?.type).toBe("table");
    if (!table || table.type !== "table") {
      throw new Error("fixture deve expor tabela");
    }
    expect(table.rows).toHaveLength(2);
    expect(table.rows.map((row) => row.product_code)).toEqual([
      "10080047",
      "10080055",
    ]);

    const body = resolveRichTextBody("", multiStockToolCalls);

    expect(body).toContain("Filial 01");
    expect(body).toContain("Filial 02");
    expect(shouldShowRichPresentation("", multiStockToolCalls)).toBe(true);
  });

  it("mescla markdown textual de várias consultas", () => {
    const markdown = resolveRichTextContent("", multiStockToolCalls);

    expect(markdown).toContain("9024");
    expect(markdown).toContain("115");
  });
});

describe("tree presentation", () => {
  const analyserToolCalls = fixtureToolCalls([
    {
      name: "execute_external_action",
      metadata: {
        path: "/products/90260148/analyser",
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
            "### Informações completas do produto 90260148\n\n| Campo | Valor |\n| --- | --- |\n| Código | 90260148 |\n| Descrição | CHICOTE |\n\nA **estrutura** (BOM) está na visualização em **árvore** ou **tabela** abaixo.\n\n**Insights**\n\n- Custo padrão vigente: R$ 272,80.",
        },
      },
    },
  ]);

  const structureToolCalls = fixtureToolCalls([
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
  ]);

  it("empilha blocos complementares do analyser", () => {
    const pair = getPresentationPairFromToolCalls(analyserToolCalls);

    expect(resolvePresentationLayoutMode(analyserToolCalls, pair)).toBe("commentary-visual");
    expect(getPresentationTitle("", analyserToolCalls)).toBe(
      "Informações completas do produto 90260148",
    );

    const commentary = resolveCommentaryTextBody("", analyserToolCalls, pair);

    expect(commentary).toContain("90260148");
    expect(commentary).toContain("Insights");
    expect(commentary).not.toContain("50220013 | PI");
    expect(commentary.toLowerCase()).toContain("estrutura");
  });

  it("remove markdown duplicado da estrutura quando há árvore", () => {
    const markdown =
      "Perfil do produto.\n\n**Estrutura do produto 90260148**\n\n| Código | Descrição |\n| --- | --- |\n| 50220013 | PI |\n\n**Insights**\n\n- Item 1.";

    expect(stripRedundantStructureFromMarkdown(markdown)).toBe(
      "Perfil do produto.\n\n**Insights**\n\n- Item 1.",
    );
  });

  it("remove dump técnico de inspeção do markdown", () => {
    const markdown =
      "**Plano de inspeção**\n\n- Product=90260140, Nível=0, Qp6=[{'QP6_PRODUT': '90260140'}]\n\n| Op. | Ensaio |\n| --- | --- |";

    expect(stripRedundantInspectionDumpFromMarkdown(markdown)).toBe(
      "**Plano de inspeção**\n\n| Op. | Ensaio |\n| --- | --- |",
    );
  });

  it("remove bloco de cobertura duplicado do comentário", () => {
    const markdown =
      "Produtos pai (onde é usado)\n\n> **Cobertura dos dados:** Exibindo página 1 de 3.";

    expect(stripCoverageNoticeFromMarkdown(markdown)).toBe("Produtos pai (onde é usado)");
    expect(
      resolveCommentaryTextBody(
        markdown,
        fixtureToolCalls([
          {
            name: "execute_external_action",
            metadata: {
              ok: true,
              dataCoverageNotice: {
                kind: "pagination",
                message: "Exibindo página 1 de 3.",
              },
              treePresentation: {
                type: "tree",
                title: "Onde é usado",
                root: { id: "1", label: "10080022", children: [] },
              },
            },
          },
        ]),
      ),
    ).toBe("Produtos pai (onde é usado)");
  });

  it("extrai estado de paginação dos metadados da ferramenta", () => {
    const state = getPaginationStateFromToolCalls(
      fixtureToolCalls([
        {
          name: "execute_external_action",
          metadata: {
            ok: true,
            dataCoverageNotice: {
              kind: "pagination",
              message: "Parcial",
              details: {
                pagination: {
                  page: 1,
                  pageSize: 25,
                  total: 419,
                  totalPages: 17,
                },
              },
            },
          },
        },
      ]),
    );

    expect(state).toEqual({
      page: 1,
      pageSize: 25,
      total: 419,
      totalPages: 17,
      hasPrevious: false,
      hasNext: true,
    });
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
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          textPresentation: {
            type: "markdown",
            markdown: "### Faturamento\n\n**Valor faturado:** R$ 21.024,26",
          },
        },
      },
    ]);

    expect(shouldShowActionResults("", toolCalls)).toBe(false);
  });
});
