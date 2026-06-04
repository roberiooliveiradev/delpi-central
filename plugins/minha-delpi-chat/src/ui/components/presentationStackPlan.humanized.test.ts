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
});
