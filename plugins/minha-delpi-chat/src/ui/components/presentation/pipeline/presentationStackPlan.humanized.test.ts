import { describe, expect, it } from "vitest";

import { buildCanonicalStackSegments } from "./presentationStackBlueprint";
import type { AssistantContentSegment } from "../../message/assistantContentTypes";
import { getStackPresentationPlanFromToolCalls, planUsesHumanizedSections } from "./presentationStackPlan";

describe("presentationStackPlan humanized gating", () => {
  it("não injeta seções humanizadas fora do analyser", () => {
    const commentary = "### Estoque\n\n**Destaques**\n\n- Saldo positivo.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Estoque por filial",
          columns: [{ key: "branch", label: "Filial" }],
          rows: [{ branch: "01" }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90260149/stock",
          stackPresentationPlan: {
            presentationProfile: "generic_stack",
            humanizedSections: false,
            profileFirst: true,
            narrativeOrder: ["lead", "profileTables", "highlights", "operationalTables"],
            tableRoleOrder: ["profile", "stock"],
          },
        },
      },
    ] as never;

    const plan = getStackPresentationPlanFromToolCalls(toolCalls);

    expect(planUsesHumanizedSections(plan)).toBe(false);

    const segments = buildCanonicalStackSegments(
      commentary,
      visuals,
      (prose) => [{ kind: "markdown", markdown: prose }],
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    expect(segments.some((segment) => segment.kind === "stackSection")).toBe(false);
  });

  it("injeta seções humanizadas para perfil kpi_series da API", () => {
    const commentary =
      "### Taxa de Conversão de Vendas\n\n<!-- section:scope -->\n\nTaxa de Conversão de Vendas: indicador com 3 métrica(s) disponível(is).";
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
          path: "/commercial/closing-rate",
          stackPresentationPlan: {
            presentationProfile: "kpi_series",
            humanizedSections: true,
            sectionVisibility: {
              scope: true,
              structure: true,
            },
            sectionFraming: {
              scope: "Indicador ou série temporal retornado pela consulta.",
              structure: "Visualização gráfica ou cartões do indicador.",
            },
            narrativeOrder: ["lead", "tailVisuals"],
            tailVisualOrder: ["kpi"],
          },
        },
      },
    ] as never;

    const plan = getStackPresentationPlanFromToolCalls(toolCalls);

    expect(plan.presentationProfile).toBe("kpi_series");
    expect(planUsesHumanizedSections(plan)).toBe(true);

    const segments = buildCanonicalStackSegments(
      commentary,
      visuals,
      (prose) => [{ kind: "markdown", markdown: prose }],
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    expect(
      segments.some(
        (segment) => segment.kind === "stackSection" && segment.section.id === "scope",
      ),
    ).toBe(true);
    expect(
      segments.some(
        (segment) =>
          segment.kind === "markdown" &&
          segment.markdown.includes("Indicador ou série temporal"),
      ),
    ).toBe(true);
  });

  it("não injeta divisões numeradas em summary_then_evidence", () => {
    const commentary =
      "### Status fabril\n\nSituação consolidada: **PA PRODUZIDO**.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Produção (PA / PI / OP / apontamentos)",
          role: "list",
          columns: [{ key: "op", label: "OP" }],
          rows: [{ op: "001" }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90262404/factory-status",
          presentationDecision: { presentationMode: "summary_then_evidence" },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            humanizedSections: true,
            profileFirst: false,
            narrativeOrder: ["lead", "operationalTables"],
            tableRoleOrder: ["stock", "list"],
            sectionVisibility: { guide: true, scope: true },
            sectionFraming: {
              guide: "As ordens e apontamentos de produção detalham o que já foi fabricado.",
            },
          },
        },
      },
    ] as never;

    const segments = buildCanonicalStackSegments(
      commentary,
      visuals,
      (prose) => [{ kind: "markdown", markdown: prose }],
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    expect(segments.some((segment) => segment.kind === "stackSection")).toBe(false);
    expect(
      segments.some(
        (segment) =>
          segment.kind === "markdown" &&
          segment.markdown.includes("ordens e apontamentos"),
      ),
    ).toBe(true);
    expect(segments.some((segment) => segment.kind === "table")).toBe(true);
  });

  it("injeta árvore nativa no tail em summary_then_evidence automático", () => {
    const commentary = "### Status fabril\n\nSituação consolidada.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura fabril",
          root: { id: "90262404", label: "Produto 90262404", children: [] },
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90262404/factory-status",
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            humanizedSections: true,
            narrativeOrder: ["lead", "tailVisuals"],
            tailVisualOrder: ["tree"],
          },
        },
      },
    ] as never;

    const segments = buildCanonicalStackSegments(
      commentary,
      visuals,
      (prose) => [{ kind: "markdown", markdown: prose }],
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
    expect(segments.some((segment) => segment.kind === "stackSection")).toBe(false);
  });

  it("não monta dashboard quando o payload pruned não inclui o segmento", () => {
    const commentary = "### Status fabril\n\nSituação consolidada.";
    const visuals: AssistantContentSegment[] = [
      {
        kind: "tree",
        presentation: {
          type: "tree",
          title: "Estrutura fabril",
          root: { id: "90262404", label: "Produto 90262404", children: [] },
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          path: "/products/90262404/factory-status",
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            narrativeOrder: ["lead", "operationalTables", "tailVisuals"],
            tailVisualOrder: ["tree", "chart"],
            renderHints: {
              suppressedKinds: ["dashboard"],
            },
          },
        },
      },
    ] as never;

    const segments = buildCanonicalStackSegments(
      commentary,
      visuals,
      (prose) => [{ kind: "markdown", markdown: prose }],
      (target, segment) => {
        target.push(segment);
      },
      toolCalls,
    );

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
    expect(segments.some((segment) => segment.kind === "dashboard")).toBe(false);
  });
});
