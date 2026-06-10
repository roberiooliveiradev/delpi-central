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
});
