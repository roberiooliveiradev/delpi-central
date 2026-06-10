import { describe, expect, it } from "vitest";

import { buildCanonicalStackSegments } from "./presentationStackBlueprint";
import type { AssistantContentSegment } from "./assistantContentTypes";
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
});
