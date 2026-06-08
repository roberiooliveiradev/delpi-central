import { describe, expect, it } from "vitest";

import { buildCanonicalStackSegments } from "./presentationStackBlueprint";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { buildStackSectionChrome, isStackSectionVisible } from "./presentationStackSections";
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
            presentationProfile: "product_analyser",
            humanizedSections: true,
            profileFirst: true,
            attentionLast: true,
            sectionVisibility: {
              scope: true,
              profile: true,
              highlights: true,
              guide: true,
              inspection: false,
              structure: true,
              attention: true,
            },
            sectionFraming: {
              scope: "Visão integrada do produto 90260149.",
              profile: "Cadastro do item na tabela abaixo.",
              highlights: "Leitura rápida do que mais importa.",
              guide: "Operações de fabricação na tabela.",
              structure: "Composição em árvore abaixo.",
              attention: "Validar antes de decidir.",
            },
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

    const numberedTitles = filterSegmentsByVisualKind(segments, null)
      .filter((segment) => segment.kind === "stackSection")
      .map((segment) => (segment.kind === "stackSection" ? segment.section.title : ""));

    expect(numberedTitles[0]).toMatch(/^1\.\s/);
    expect(numberedTitles[0]).toContain("Escopo");
    expect(numberedTitles[1]).toMatch(/^2\.\s/);
    expect(numberedTitles[1]).toContain("Ficha cadastral");
    expect(numberedTitles[2]).toMatch(/^3\.\s/);
    expect(numberedTitles[2]).toContain("Destaques");
    expect(numberedTitles[3]).toMatch(/^4\.\s/);
    expect(numberedTitles[3]).toContain("Roteiro");
    expect(numberedTitles.some((title) => title.includes("Estrutura"))).toBe(true);
    expect(numberedTitles.some((title) => title.includes("Inspeção"))).toBe(false);
    expect(numberedTitles.at(-1)).toMatch(/^\d+\.\s/);
    expect(numberedTitles.at(-1)).toContain("Alertas");

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

  it("renumera seções quando escopo e inspeção estão ausentes", () => {
    const segments = [
      { kind: "stackSection", section: buildStackSectionChrome("profile") },
      { kind: "stackSection", section: buildStackSectionChrome("highlights") },
      { kind: "stackSection", section: buildStackSectionChrome("guide") },
      { kind: "stackSection", section: buildStackSectionChrome("structure") },
      { kind: "stackSection", section: buildStackSectionChrome("attention") },
    ] as never;

    const titles = filterSegmentsByVisualKind(segments, null)
      .filter((segment) => segment.kind === "stackSection")
      .map((segment) => (segment.kind === "stackSection" ? segment.section.title : ""));

    expect(titles).toEqual([
      "1. Ficha cadastral",
      "2. Síntese executiva (Destaques)",
      "3. Roteiro de produção",
      "4. Estrutura (BOM)",
      "5. Alertas e divergências",
    ]);
  });

  it("filtra seções por aba da toolbar", () => {
    const profileSection = buildStackSectionChrome("profile");

    expect(isStackSectionVisible(profileSection, "table")).toBe(true);
    expect(isStackSectionVisible(profileSection, "text")).toBe(false);

    const segments: AssistantContentSegment[] = [
      { kind: "stackSection", section: buildStackSectionChrome("scope") },
      { kind: "stackSection", section: profileSection },
      { kind: "markdown", markdown: "texto" },
    ];

    const textOnly = filterSegmentsByVisualKind(segments, "text");

    expect(textOnly.some((segment) => segment.kind === "stackSection")).toBe(true);
    expect(
      textOnly.filter((segment) => segment.kind === "stackSection").length,
    ).toBe(1);
  });
});
