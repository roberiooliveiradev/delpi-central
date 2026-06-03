import { describe, expect, it } from "vitest";

import {
  buildAssistantContentSegments,
  dedupeSqlFencesInMarkdown,
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
});
