import { describe, expect, it } from "vitest";

import {
  hasRichStackPresentation,
  stripRichUiRedundantProseFromMarkdown,
} from "../chatPresentation";
import { fixtureToolCalls } from "../message/testFixtures";

describe("richStackPresentation", () => {
  it("detecta stack em faturamento com tabela e gráfico", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/commercial/billing",
          presentationDecision: { layoutMode: "stack", availableViews: ["text", "table", "chart"] },
          tablePresentation: {
            type: "table",
            title: "Faturamento",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01" }],
          },
          chartPresentation: {
            type: "chart",
            chartType: "bar",
            title: "Faturamento",
            data: [{ branch: "01", total: 1 }],
          },
        },
      },
    ]);

    expect(hasRichStackPresentation(toolCalls)).toBe(true);
  });

  it("remove tabela markdown duplicada em apresentação rica", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          presentationDecision: { layoutMode: "stack" },
          tablePresentation: {
            type: "table",
            title: "Resultado",
            columns: [{ key: "a", label: "A" }],
            rows: [{ a: "1" }],
          },
        },
      },
    ]);
    const markdown = "### Resultado\n\n| A |\n| --- |\n| 1 |\n\n**Destaques**\n\n- OK.";

    const compact = stripRichUiRedundantProseFromMarkdown(markdown, toolCalls);

    expect(compact).not.toContain("| A |");
    expect(compact).toContain("**Destaques**");
  });

  it("remove composição em bloco de código quando árvore nativa existe", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          presentationDecision: { layoutMode: "stack" },
          treePresentation: {
            type: "tree",
            title: "Estrutura fabril",
            root: { id: "90262404", label: "Produto 90262404", children: [] },
          },
        },
      },
    ]);
    const markdown =
      "### Status\n\nVisão integrada na fábrica.\n\n**Composição**\n\n```text\nProduto 90262404\n└── 10160001 (MP)\n```";

    const compact = stripRichUiRedundantProseFromMarkdown(markdown, toolCalls);

    expect(compact).not.toContain("```text");
    expect(compact).not.toContain("**Composição**");
    expect(compact).toContain("Visão integrada");
  });
});
