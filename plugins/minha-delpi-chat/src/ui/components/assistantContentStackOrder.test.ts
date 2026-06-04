import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./assistantContentSegments";
import { fixtureToolCalls } from "./testFixtures";

describe("assistantContentStackOrder", () => {
  it("intercala narrativa, tabelas e árvore por seções em layout stack", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/90260149/analyser",
          presentationDecision: {
            layoutMode: "stack",
            selected: "tree",
            visualOrder: ["text", "table", "tree"],
          },
          textPresentation: {
            type: "markdown",
            markdown:
              "### Informações completas do produto 90260149\n\n" +
              "**Destaques**\n\n- Estrutura com 6 itens.\n\n" +
              "**Pontos de atenção encontrados na API:**\n\n1. Bloqueio.",
          },
          presentation: {
            type: "tree",
            title: "Estrutura do produto 90260149",
            root: { id: "90260149", label: "90260149", children: [] },
          },
          tablePresentations: [
            {
              type: "table",
              title: "Roteiro de produção — 90260149",
              columns: [{ key: "product_code", label: "Produto" }],
              rows: [{ product_code: "90260149" }],
            },
            {
              type: "table",
              title: "Produto 90260149",
              columns: [{ key: "campo", label: "Campo" }],
              rows: [{ campo: "Código", valor: "90260149" }],
            },
          ],
        },
      },
    ]);

    const segments = buildAssistantContentSegments("", toolCalls);
    const kinds = segments.map((segment) => segment.kind);
    const destaqueIndex = segments.findIndex(
      (segment) =>
        segment.kind === "markdown" &&
        segment.markdown.includes("**Destaques**"),
    );
    const roteiroIndex = segments.findIndex(
      (segment) =>
        segment.kind === "table" &&
        String(segment.presentation.title || "").includes("Roteiro"),
    );
    const pontosIndex = segments.findIndex(
      (segment) =>
        segment.kind === "markdown" &&
        segment.markdown.includes("**Pontos de atenção"),
    );
    const treeIndex = kinds.indexOf("tree");

    expect(destaqueIndex).toBeGreaterThanOrEqual(0);
    expect(roteiroIndex).toBeGreaterThan(destaqueIndex);
    expect(pontosIndex).toBeGreaterThan(roteiroIndex);
    expect(treeIndex).toBeGreaterThan(pontosIndex);
  });
});
