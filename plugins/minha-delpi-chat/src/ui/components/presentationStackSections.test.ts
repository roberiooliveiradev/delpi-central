import { describe, expect, it } from "vitest";

import { buildCanonicalStackSegments } from "./presentationStackBlueprint";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { isStackSectionVisible, STACK_SECTION_BY_ID } from "./presentationStackSections";
import { filterSegmentsByVisualKind } from "./assistantContentVisualFormats";

function parseMarkdown(prose: string): AssistantContentSegment[] {
  return [{ kind: "markdown", markdown: prose }];
}

describe("presentationStackSections", () => {
  it("intercala seções humanizadas na ordem do analyser", () => {
    const commentary = [
      "### Informações completas do produto 90260149",
      "",
      "Análise integrada do cadastro, roteiro, inspeção e BOM.",
      "",
      "**Destaques**",
      "",
      "- Estrutura com 6 itens.",
      "",
      "**Pontos de atenção encontrados na API:**",
      "",
      "1. Bloqueio «2».",
    ].join("\n");

    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Produto 90260149",
          columns: [
            { key: "campo", label: "Campo" },
            { key: "valor", label: "Valor" },
          ],
          rows: [{ campo: "Código", valor: "90260149" }],
        },
      },
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
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura do produto 90260149",
          nodes: [{ id: "root", label: "90260149" }],
        },
      },
    ];

    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90260149/analyser",
          presentationDecision: { layoutMode: "stack" },
          stackPresentationPlan: {
            profileFirst: true,
            attentionLast: true,
            narrativeOrder: [
              "lead",
              "profileTables",
              "highlights",
              "operationalTables",
              "tailVisuals",
              "attention",
            ],
            tableRoleOrder: ["profile", "guide", "inspection"],
            tailVisualOrder: ["tree"],
          },
        },
      },
    ] as never;

    const segments = buildCanonicalStackSegments(
      commentary,
      visuals,
      parseMarkdown,
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    const sectionTitles = segments
      .filter((segment) => segment.kind === "stackSection")
      .map((segment) => (segment.kind === "stackSection" ? segment.section.title : ""));

    expect(sectionTitles[0]).toContain("Escopo");
    expect(sectionTitles[1]).toContain("Ficha cadastral");
    expect(sectionTitles[2]).toContain("Destaques");
    expect(sectionTitles[3]).toContain("Roteiro");
    expect(sectionTitles.some((title) => title.includes("Estrutura"))).toBe(true);
    expect(sectionTitles.at(-1)).toContain("Alertas");

    const profileIndex = segments.findIndex(
      (segment) => segment.kind === "table" && segment.presentation.title?.startsWith("Produto "),
    );
    const scopeIndex = segments.findIndex(
      (segment) => segment.kind === "stackSection" && segment.section.id === "scope",
    );
    const attentionIndex = segments.findIndex(
      (segment) => segment.kind === "stackSection" && segment.section.id === "attention",
    );
    const treeIndex = segments.findIndex((segment) => segment.kind === "tree");

    expect(scopeIndex).toBeLessThan(profileIndex);
    expect(profileIndex).toBeLessThan(treeIndex);
    expect(treeIndex).toBeLessThan(attentionIndex);
  });

  it("filtra seções por aba da toolbar", () => {
    expect(isStackSectionVisible(STACK_SECTION_BY_ID.profile, "table")).toBe(true);
    expect(isStackSectionVisible(STACK_SECTION_BY_ID.profile, "text")).toBe(false);

    const segments: AssistantContentSegment[] = [
      { kind: "stackSection", section: STACK_SECTION_BY_ID.scope },
      { kind: "stackSection", section: STACK_SECTION_BY_ID.profile },
      { kind: "markdown", markdown: "texto" },
    ];

    const textOnly = filterSegmentsByVisualKind(segments, "text");

    expect(textOnly.some((segment) => segment.kind === "stackSection")).toBe(true);
    expect(
      textOnly.filter((segment) => segment.kind === "stackSection").length,
    ).toBe(1);
  });
});
