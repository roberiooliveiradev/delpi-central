import { describe, expect, it } from "vitest";

import {
  buildAssistantContentSegments,
  dedupeSqlFencesInMarkdown,
  isPresentationHeadingTitle,
  parseMarkdownAndCodeSegments,
} from "./assistantContentSegments";

describe("assistantContentSegments", () => {
  it("remove blocos SQL duplicados", () => {
    const intro =
      "Segue a consulta em SQL (somente leitura, sem executar no sistema). " +
      "Ajuste sufixo de tabela (ex.: SA1010) conforme o ambiente:";
    const input =
      "```sql\nSELECT A1_COD FROM SA1010\n```\n\n```sql\nSELECT A1_COD FROM SA1010\n```";

    expect(dedupeSqlFencesInMarkdown(input)).toBe(
      `${intro}\n\n\`\`\`sql\nSELECT A1_COD FROM SA1010\n\`\`\``,
    );
  });

  it("remove parágrafo repetido após o bloco SQL", () => {
    const before =
      "Com base nas informações que você forneceu, não há diretamente nenhuma tabela chamada SA1 em um contexto padrão do Delpi.";
    const input = `${before}\n\n\`\`\`sql\nSELECT A1_COD\n\`\`\`\n\n${before}`;

    expect(dedupeSqlFencesInMarkdown(input)).toBe(
      `${before}\n\n\`\`\`sql\nSELECT A1_COD\n\`\`\``,
    );
  });

  it("remove intro SQL duplicada após deduplicar fences", () => {
    const intro =
      "Segue a consulta em SQL (somente leitura, sem executar no sistema). " +
      "Ajuste sufixo de tabela (ex.: SA1010) conforme o ambiente:";
    const input = `${intro}\n\n\`\`\`sql\nSELECT A1_COD\n\`\`\`\n\n${intro}`;

    expect(dedupeSqlFencesInMarkdown(input)).toBe(
      `${intro}\n\n\`\`\`sql\nSELECT A1_COD\n\`\`\``,
    );
  });

  it("colapsa blocos SQL duplicados sem repetir intro e explicação", () => {
    const intro =
      "Segue a consulta em SQL (somente leitura, sem executar no sistema). " +
      "Ajuste sufixo de tabela (ex.: SA1010) conforme o ambiente:";
    const explanation =
      'Esta consulta SQL selecionará apenas o código e o nome dos clientes ' +
      'que estão no status de "Ativo" na tabela SA1.';
    const sql = "SELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''";
    const input = [
      `${intro}\n\n\`\`\`sql\n${sql}\n\`\`\`\n\n${explanation}`,
      `${intro}\n\n\`\`\`sql\n${sql}\n\`\`\`\n\n${explanation}`,
    ].join("\n\n");

    const output = dedupeSqlFencesInMarkdown(input);

    expect(output.match(/```sql/gi)?.length).toBe(1);
    expect(output.match(/Segue a consulta em SQL/gi)?.length).toBe(1);
    expect(output.match(/Esta consulta SQL/gi)?.length).toBe(1);
  });

  it("colapsa fence SQL inline duplicado com bloco renderizável", () => {
    const before =
      "Com base nas permissões do papel Superadministrador que você possui, " +
      "você pode consultar a tabela SA1 para obter apenas os códigos e nomes " +
      "dos clientes ativos. Aqui está uma consulta SQL simples para isso:";
    const explanation =
      "Esta consulta retornará apenas os códigos e nomes dos clientes cujo status é " +
      "'ATIVO'. Certifique-se de que você tem permissões suficientes para acessar " +
      "a tabela SA1.";
    const inlineSql = "SELECT A1_COD, A1_NOME FROM SA1010 WHERE D_E_L_E_T_ = ''";
    const blockSql = "SELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''";
    const input =
      `${before} \`\`\`sql ${inlineSql} \`\`\` ${explanation}\n\n` +
      `${before}\n\n\`\`\`sql\n${blockSql}\n\`\`\`\n\n${explanation}`;

    const output = dedupeSqlFencesInMarkdown(input);

    expect(output.match(/```sql/gi)?.length).toBe(1);
    expect(output.match(/Com base nas permissões/gi)?.length).toBe(1);
    expect(output.match(/Esta consulta retornará/gi)?.length).toBe(1);
  });

  it("separa texto explicativo e bloco SQL", () => {
    const segments = parseMarkdownAndCodeSegments(
      "Segue a consulta:\n\n```sql\nSELECT A1_COD, A1_NOME FROM SA1010\n```",
    );

    expect(segments).toHaveLength(2);
    expect(segments[0]).toMatchObject({ kind: "markdown" });
    expect(segments[1]).toMatchObject({ kind: "code", language: "sql" });
  });

  it("insere marcador [[table]] no meio do texto", () => {
    const segments = buildAssistantContentSegments(
      "Resumo inicial.\n\n[[table]]\n\nConclusão.",
      [
        {
          name: "execute_external_action",
          metadata: {
            presentation: {
              type: "table",
              title: "Estoque",
              columns: [{ key: "branch", label: "Filial" }],
              rows: [{ branch: "01" }],
            },
          },
        },
      ],
    );

    expect(segments.some((item) => item.kind === "markdown")).toBe(true);
    expect(segments.some((item) => item.kind === "table")).toBe(true);
  });

  it("com proseCompositionSource=llm segue renderPlan intercalado (sem reordenar)", () => {
    const segments = buildAssistantContentSegments("fallback [[tree]] no markdown", [
      {
        name: "execute_external_action",
        metadata: {
          proseCompositionSource: "llm",
          treePresentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "1", label: "PA", children: [] },
          },
          tablePresentation: {
            type: "table",
            title: "Estoque",
            columns: [{ key: "code", label: "Código" }],
            rows: [{ code: "10080109" }],
          },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            proseCompositionSource: "llm",
            segments: [
              {
                kind: "markdown",
                slot: "assistantProse",
                source: "assistantMessage",
                text: "Lead da composição.",
              },
              { kind: "tree", slot: "tree", source: "treePresentation" },
              {
                kind: "markdown",
                slot: "assistantProse",
                source: "assistantMessage",
                text: "Comentário de estoque.",
              },
              { kind: "table", slot: "table", source: "tablePresentation", index: 1 },
            ],
          },
        },
      },
    ]);

    const kinds = segments.map((item) => item.kind);

    expect(kinds).toEqual(["markdown", "tree", "markdown", "table"]);
    expect(String((segments[0] as { markdown?: string }).markdown || "")).toContain(
      "Lead da composição",
    );
  });

  it("não trata conteúdo inteiro de resposta SQL como título de apresentação", () => {
    const intro =
      "Segue a consulta em SQL (somente leitura, sem executar no sistema). " +
      "Ajuste sufixo de tabela (ex.: SA1010) conforme o ambiente:";
    const fullAnswer = `${intro}\n\n\`\`\`sql\nSELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''\n\`\`\``;

    expect(isPresentationHeadingTitle(fullAnswer)).toBe(false);
  });

  it("aceita títulos curtos de uma linha como heading de apresentação", () => {
    expect(isPresentationHeadingTitle("Estoque por filial")).toBe(true);
    expect(isPresentationHeadingTitle("")).toBe(false);
    expect(isPresentationHeadingTitle("Linha 1\nLinha 2")).toBe(false);
    expect(isPresentationHeadingTitle("Tem ```sql aqui")).toBe(false);
  });

  it("renderiza saudação com negrito via markdown, não como heading cru", () => {
    const greeting = "Olá! Sou o **Agente Minha DELPI**. O que vamos consultar?";
    const segments = buildAssistantContentSegments(greeting, []);

    expect(isPresentationHeadingTitle(greeting)).toBe(false);
    expect(segments).toHaveLength(1);
    expect(segments[0]?.kind).toBe("markdown");
    if (segments[0]?.kind === "markdown") {
      expect(segments[0].markdown).toBe(greeting);
    }
  });

  it("modo texto mantém quebras do outline de árvore em bloco text", () => {
    const markdown =
      "### Estrutura do produto 90260149\n\n**Composição**\n\n```text\n90260149 PA 1 MI — RAIZ\n└── 50230130 PI 1 MI — COMP\n    └── 10080109 MP 1 PC — SUB\n```";
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
            markdown,
          },
        },
      },
    ] as const;

    const segments = buildAssistantContentSegments("", [...toolCalls]);
    const prose = segments
      .filter((item) => item.kind === "markdown" || item.kind === "code")
      .map((item) => (item.kind === "markdown" ? item.markdown : item.code))
      .join("\n");

    expect(prose).toMatch(/90260149 PA 1 MI — RAIZ\n└── 50230130 PI 1 MI — COMP/);
    expect(prose).toContain("    └── 10080109 MP 1 PC — SUB");
  });

  it("prioriza tabela nativa em layout single com selected=table", () => {
    const longMarkdown =
      "### Estoque\n\n<!-- section:scope -->\n\nDetalhamento longo em prosa.";
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            selected: "table",
            layoutMode: "single",
            visualOrder: ["table"],
          },
          textPresentation: {
            type: "markdown",
            markdown: longMarkdown,
          },
          presentation: {
            type: "table",
            title: "Posições por filial e armazém",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01", current_quantity: 455000 }],
          },
        },
      },
    ];

    const segments = buildAssistantContentSegments(
      "Posições por filial e armazém",
      toolCalls,
    );

    expect(segments.some((item) => item.kind === "table")).toBe(true);
    expect(
      segments.some(
        (item) =>
          item.kind === "markdown" &&
          item.markdown.includes("Detalhamento longo em prosa"),
      ),
    ).toBe(false);
  });

  it("renderPlan só com prosa não monta visuais latentes do metadata", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            selected: "text",
            layoutMode: "single",
            presentationMode: "summary_then_evidence",
          },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [{ kind: "markdown", slot: "lead", source: "textPresentation" }],
          },
          textPresentation: {
            type: "markdown",
            markdown: "### Status produtivo\n\nOP em andamento.",
          },
          kpiPresentation: {
            type: "kpi",
            title: "Indicadores",
            items: [],
          },
          treePresentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "90269002", label: "90269002", children: [] },
          },
        },
      },
    ];

    const segments = buildAssistantContentSegments("", toolCalls);

    expect(segments.every((item) => item.kind === "markdown" || item.kind === "code")).toBe(true);
    expect(segments.some((item) => item.kind === "tree" || item.kind === "kpi")).toBe(false);
  });

  it("modo Texto explícito inclui tabelas do metadata quando o markdown não as embute", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          explicitSessionFormat: "text",
          textPresentation: {
            type: "markdown",
            title: "Status completo na fábrica — 90262404",
            markdown:
              "### Status completo na fábrica — 90262404\n\nSituação consolidada: **PA PRODUZIDO**",
          },
          tablePresentations: [
            {
              type: "table",
              title: "Panorama fabril",
              columns: [
                { key: "campo", label: "Campo" },
                { key: "valor", label: "Valor" },
              ],
              rows: [{ campo: "OPs de PA", valor: "305" }],
            },
          ],
        },
      },
    ];

    const segments = buildAssistantContentSegments("", toolCalls);
    const markdown = segments
      .filter((item) => item.kind === "markdown")
      .map((item) => item.markdown)
      .join("\n");

    expect(markdown).toContain("|");
    expect(markdown).toContain("Panorama fabril");
    expect(markdown).toContain("305");
  });

  it("modo Texto explícito mantém segmento download dos downloadArtifacts", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          explicitSessionFormat: "text",
          downloadArtifacts: [
            {
              href: "/apps/api-delpi/products/90261699/structure/excel?format=xlsx",
              filename: "Estrutura_90261699.xlsx",
              label: "Baixar Estrutura_90261699.xlsx",
              contentType:
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
          ],
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [
              { kind: "markdown", slot: "lead", source: "assistantMessage" },
              { kind: "download", slot: "artifacts", source: "downloadArtifacts" },
            ],
          },
          presentationDecision: {
            selected: "text",
            fallback: "text",
            layoutMode: "single",
          },
        },
      },
    ];

    const segments = buildAssistantContentSegments(
      "Arquivo pronto para download: **Estrutura_90261699.xlsx**.",
      toolCalls,
    );

    const download = segments.find((item) => item.kind === "download");

    expect(download).toBeDefined();
    expect(download?.kind === "download" && download.artifacts[0]?.filename).toBe(
      "Estrutura_90261699.xlsx",
    );
  });

  it("decisão text sem renderPlan mantém segmento download", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          downloadArtifacts: [
            {
              href: "/apps/api-delpi/products/90261699/structure/excel?format=xlsx",
              filename: "Estrutura_90261699.xlsx",
              label: "Baixar Estrutura_90261699.xlsx",
            },
          ],
          presentationDecision: {
            selected: "text",
            fallback: "text",
            layoutMode: "single",
          },
        },
      },
    ];

    const segments = buildAssistantContentSegments("Arquivo pronto.", toolCalls);

    expect(segments.some((item) => item.kind === "download")).toBe(true);
  });

  it("renderPlan primary composto (estoque tabela + enrichment KPI) exibe ambos", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          compositionRole: "primary",
          path: "/products/10080001/stock",
          presentationDecision: { selected: "table", layoutMode: "stack" },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "assistantMessage" },
              { kind: "table", slot: "primary", source: "tablePresentation" },
              { kind: "kpi", slot: "enrichment", source: "kpiPresentation" },
            ],
          },
          tablePresentation: {
            type: "table",
            title: "Estoque do produto",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01" }, { branch: "02" }],
          },
          kpiPresentation: {
            type: "kpi",
            title: "Indicador",
            cards: [{ key: "documents", label: "Documentos", value: 67 }],
          },
        },
      },
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          compositionRole: "enrichment",
          path: "/products/10080001/sales",
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [{ kind: "markdown", slot: "lead", source: "assistantMessage" }],
          },
        },
      },
    ];

    const segments = buildAssistantContentSegments(
      "O produto **10080001** tem saldo disponível.",
      toolCalls,
    );
    const kinds = segments.map((item) => item.kind);

    expect(kinds).toContain("table");
    expect(kinds).toContain("kpi");
  });

  it("F06 columns: path /system/tables/.../columns com presentation table aparece na bolha", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/system/tables/SB1010/columns",
          preferredFormat: "table",
          presentationDecision: {
            selected: "table",
            layoutMode: "single",
          },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [
              { kind: "decision", slot: "lead", source: "dataAnswer" },
              { kind: "table", slot: "primary", source: "presentation" },
            ],
          },
          presentation: {
            type: "table",
            title: "Colunas (SX3)",
            columns: [
              { key: "X3_CAMPO", label: "Campo" },
              { key: "X3_TITULO", label: "Título" },
            ],
            rows: [
              { X3_CAMPO: "B1_COD", X3_TITULO: "Codigo" },
              { X3_CAMPO: "B1_DESC", X3_TITULO: "Descricao" },
            ],
          },
        },
      },
    ];

    const segments = buildAssistantContentSegments(
      "**318** registro(s) no catálogo de metadados.",
      toolCalls as never,
    );

    expect(segments.some((item) => item.kind === "table")).toBe(true);
  });
});
