import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./assistantContentSegments";
import {
  buildInterleavedStackSegments,
  partitionCommentarySections,
} from "./assistantContentInterleave";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { fixtureToolCalls } from "./testFixtures";

function appendUnique(
  segments: AssistantContentSegment[],
  segment: AssistantContentSegment,
): void {
  const exists = segments.some(
    (item) => item.kind === segment.kind && JSON.stringify(item) === JSON.stringify(segment),
  );

  if (!exists) {
    segments.push(segment);
  }
}

describe("assistantContentInterleave", () => {
  it("particiona lead sem vazar marcadores section:*", () => {
    const sections = partitionCommentarySections(
      "### Escopo\n\n<!-- section:scope -->\n\n10070012 — CABO.\n\n<!-- section:highlights -->\n\n**Destaques**\n\n- Um.",
    );

    expect(sections.lead).not.toContain("<!-- section:");
    expect(sections.lead).toContain("10070012");
  });

  it("particiona destaques e pontos de atenção", () => {
    const sections = partitionCommentarySections(
      "### Título\n\n**Destaques**\n\n- Um.\n\n**Pontos de atenção encontrados na API:**\n\n1. Dois.",
    );

    expect(sections.hasSectionBreaks).toBe(true);
    expect(sections.lead).toContain("Título");
    expect(sections.destaques).toContain("Destaques");
    expect(sections.pontos).toContain("Pontos de atenção");
  });

  it("ordena ficha, destaques, roteiro, árvore e pontos no final", () => {
    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Roteiro de produção — 90260149",
          columns: [{ key: "product_code", label: "Produto" }],
          rows: [{ product_code: "90260149" }],
        },
      },
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Produto 90260149",
          columns: [{ key: "campo", label: "Campo" }],
          rows: [{ campo: "Código", valor: "90260149" }],
        },
      },
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura do produto 90260149",
          root: { id: "90260149", label: "90260149", children: [] },
        },
      },
    ];

    const segments = buildInterleavedStackSegments(
      "### Informações\n\n**Destaques**\n\n- Destaque.\n\n**Pontos de atenção encontrados na API:**\n\n1. Atenção.",
      visuals,
      (prose) => [{ kind: "markdown", markdown: prose }],
      appendUnique,
    );

    const destaqueIndex = segments.findIndex(
      (segment) => segment.kind === "markdown" && segment.markdown.includes("Destaque."),
    );
    const roteiroIndex = segments.findIndex(
      (segment) =>
        segment.kind === "table" &&
        segment.presentation.title?.includes("Roteiro"),
    );
    const profileIndex = segments.findIndex(
      (segment) =>
        segment.kind === "table" && segment.presentation.title?.startsWith("Produto "),
    );
    const pontosIndex = segments.findIndex(
      (segment) => segment.kind === "markdown" && segment.markdown.includes("1. Atenção"),
    );
    const treeIndex = segments.findIndex((segment) => segment.kind === "tree");

    const leadIndex = segments.findIndex(
      (segment) =>
        segment.kind === "markdown" && segment.markdown.includes("Informações"),
    );

    expect(leadIndex).toBeGreaterThanOrEqual(0);
    expect(profileIndex).toBeGreaterThan(leadIndex);
    expect(destaqueIndex).toBeGreaterThan(profileIndex);
    expect(roteiroIndex).toBeGreaterThan(destaqueIndex);
    expect(treeIndex).toBeGreaterThan(roteiroIndex);
    expect(pontosIndex).toBeGreaterThan(treeIndex);
  });

  it("não vaza marcadores section:* nos segmentos do analyser (stack completo)", () => {
    const analyserMarkdown =
      "### Informações completas do produto 10070012\n\n" +
      "<!-- section:scope -->\n\n" +
      "**10070012** — CABO PP CIRCULAR.\n\n" +
      "<!-- section:highlights -->\n\n" +
      "**Destaques**\n\n- Custo padrão vigente: R$ 0,98.";

    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/10070012/analyser",
          presentationDecision: { layoutMode: "stack" },
          stackPresentationPlan: {
            presentationProfile: "generic_stack",
            humanizedSections: true,
            profileFirst: true,
            sectionVisibility: {
              scope: true,
              profile: true,
              highlights: true,
              guide: true,
              structure: true,
              attention: true,
            },
            narrativeOrder: [
              "lead",
              "profileTables",
              "highlights",
              "operationalTables",
              "tailVisuals",
              "attention",
            ],
          },
          textPresentation: {
            type: "markdown",
            markdown: analyserMarkdown,
          },
          tablePresentations: [
            {
              type: "table",
              title: "Produto 10070012",
              columns: [{ key: "campo", label: "Campo" }],
              rows: [{ campo: "Código", valor: "10070012" }],
            },
          ],
        },
      },
    ]);

    const segments = buildAssistantContentSegments("", toolCalls);
    const leaked = segments.some(
      (segment) =>
        segment.kind === "markdown" && /<!--\s*section:/i.test(segment.markdown),
    );

    expect(leaked).toBe(false);
  });

  it("usa marcadores [[table:n]] embutidos no markdown", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: { layoutMode: "stack" },
          textPresentation: {
            type: "markdown",
            markdown:
              "**Destaques**\n\n- Item.\n\n[[table:1]]\n\n**Pontos de atenção**\n\n1. Alerta.\n\n[[arvore]]",
          },
          presentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "1", label: "1", children: [] },
          },
          tablePresentations: [
            {
              type: "table",
              title: "Roteiro de produção — 1",
              columns: [{ key: "product_code", label: "Produto" }],
              rows: [{ product_code: "1" }],
            },
          ],
        },
      },
    ]);

    const segments = buildAssistantContentSegments("", toolCalls);
    const destaqueIndex = segments.findIndex(
      (segment) => segment.kind === "markdown" && segment.markdown.includes("- Item."),
    );
    const tableIndex = segments.findIndex((segment) => segment.kind === "table");
    const pontosIndex = segments.findIndex(
      (segment) => segment.kind === "markdown" && segment.markdown.includes("1. Alerta"),
    );
    const treeIndex = segments.findIndex((segment) => segment.kind === "tree");

    expect(destaqueIndex).toBeLessThan(tableIndex);
    expect(tableIndex).toBeLessThan(treeIndex);
    expect(treeIndex).toBeLessThan(pontosIndex);
  });
});
