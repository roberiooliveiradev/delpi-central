import { describe, expect, it } from "vitest";

import type { AssistantContentSegment } from "../../message/assistantContentTypes";
import { buildCanonicalStackSegments } from "../pipeline/presentationStackBlueprint";
import { buildSegmentsFromRenderPlan } from "./renderPlanSegmentBuilder";

function parseMarkdown(prose: string): AssistantContentSegment[] {
  return [{ kind: "markdown", markdown: prose }];
}

describe("renderPlanSegmentBuilder", () => {
  it("monta stack evidence-first a partir do renderPlan da API", () => {
    const commentary = "### Status fabril\n\nSituação consolidada.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura fabril",
          root: { id: "90262404", label: "90262404", children: [] },
        },
      },
      {
        kind: "chart",
        presentation: {
          type: "chart",
          chartType: "bar",
          title: "Saldo MP",
          data: [{ label: "MP", value: 1 }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["tree", "chart"],
            narrativeOrder: ["lead", "operationalTables", "tailVisuals"],
            renderHints: { textRenderMode: "compact", tailVisualPolicy: "allowlist" },
          },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "tree", slot: "tailVisuals", source: "treePresentation" },
              { kind: "chart", slot: "tailVisuals", source: "chartPresentation" },
            ],
          },
        },
      },
    ] as never;

    const segments = buildSegmentsFromRenderPlan(
      commentary,
      visuals,
      parseMarkdown,
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    const kinds = (segments ?? []).map((segment) => segment.kind);

    expect(kinds).toContain("markdown");
    expect(kinds).toContain("tree");
    expect(kinds).toContain("chart");
    expect(kinds).not.toContain("dashboard");
    expect(kinds).not.toContain("stackSection");
  });

  it("buildCanonicalStackSegments prioriza renderPlan quando presente", () => {
    const commentary = "### Status fabril\n\nSituação consolidada.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura fabril",
          root: { id: "90262404", label: "90262404", children: [] },
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["tree"],
            narrativeOrder: ["lead", "tailVisuals"],
          },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "tree", slot: "tailVisuals", source: "treePresentation" },
            ],
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

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
    expect(segments.some((segment) => segment.kind === "stackSection")).toBe(false);
  });

  it("não usa blueprint legado quando renderPlan v1 omite dashboard", () => {
    const commentary = "### Status fabril\n\nSituação consolidada.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura fabril",
          root: { id: "90262404", label: "90262404", children: [] },
        },
      },
      {
        kind: "dashboard",
        presentation: {
          type: "dashboard",
          title: "Painel fabril",
          panels: [],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["tree"],
            narrativeOrder: ["lead", "tailVisuals"],
          },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "tree", slot: "tailVisuals", source: "treePresentation" },
            ],
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

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
    expect(segments.some((segment) => segment.kind === "dashboard")).toBe(false);
  });

  it("não sintetiza renderPlan quando a API não enviou v1", () => {
    const commentary =
      "### Taxa de Conversão\n\n<!-- section:scope -->\n\nIndicador com 3 métricas.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "kpi",
        presentation: {
          type: "kpi",
          title: "Taxa de Conversão de Vendas",
          cards: [{ label: "Atual", value: "82,5%" }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          stackPresentationPlan: {
            humanizedSections: true,
            sectionVisibility: { scope: true, structure: true },
            sectionFraming: {
              scope: "Indicador retornado pela consulta.",
              structure: "Cartões do indicador.",
            },
            narrativeOrder: ["lead", "tailVisuals"],
            tailVisualOrder: ["kpi"],
          },
        },
      },
    ] as never;

    const segments = buildSegmentsFromRenderPlan(
      commentary,
      visuals,
      parseMarkdown,
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    expect(segments).toBeNull();
  });

  it("renderiza todas as tabelas do bundle no modo Tabela explícito", () => {
    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Estrutura do produto (BOM)",
          role: "structure",
          columns: [{ key: "component_code", label: "Componente" }],
          rows: [{ component_code: "50250258" }],
        },
      },
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Fornecedores por matéria-prima",
          role: "list",
          columns: [{ key: "supplier_code", label: "Fornecedor" }],
          rows: [{ supplier_code: "000052" }],
        },
      },
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Última compra por matéria-prima",
          role: "list",
          columns: [{ key: "invoice_number", label: "Nº nota" }],
          rows: [{ invoice_number: "015277" }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          explicitSessionFormat: "table",
          presentationDecision: {
            selected: "table",
            layoutMode: "single",
          },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [
              {
                kind: "table",
                slot: "operationalTables",
                source: "tablePresentations",
              },
            ],
          },
        },
      },
    ] as never;

    const segments = buildSegmentsFromRenderPlan(
      "",
      visuals,
      parseMarkdown,
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    const tableTitles = (segments ?? [])
      .filter((segment) => segment.kind === "table")
      .map((segment) => segment.presentation.title);

    expect(tableTitles).toEqual([
      "Estrutura do produto (BOM)",
      "Fornecedores por matéria-prima",
      "Última compra por matéria-prima",
    ]);
  });

  it("operationalTables inclui tabela profile quando cadastro veio nesse slot", () => {
    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          role: "profile",
          title: "Produto 10080045",
          columns: [
            { key: "campo", label: "Campo" },
            { key: "valor", label: "Valor" },
          ],
          rows: [{ campo: "Código", valor: "10080045" }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          llmProseDecoupled: true,
          presentationDecision: {
            selected: "table",
            layoutMode: "stack",
            presentationMode: "summary_then_evidence",
            stackPresentationPlan: {
              profileFirst: true,
              tableRoleOrder: ["profile", "guide", "inspection", "other"],
            },
          },
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "assistantMessage" },
              {
                kind: "table",
                slot: "operationalTables",
                source: "tablePresentations",
              },
            ],
          },
        },
      },
    ] as never;

    const segments =
      buildSegmentsFromRenderPlan(
        "O produto **10080045** está cadastrado como MP.",
        visuals,
        parseMarkdown,
        (target, segment) => {
          target.push(segment);
        },
        toolCalls,
      ) ?? [];

    expect(segments.some((segment) => segment.kind === "markdown")).toBe(true);
    expect(segments.some((segment) => segment.kind === "table")).toBe(true);
  });
});
