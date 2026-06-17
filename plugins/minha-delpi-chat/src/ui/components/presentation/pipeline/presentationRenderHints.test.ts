import { describe, expect, it } from "vitest";

import {
  getPresentationRenderHintsFromToolCalls,
  getRenderPlanAllowedVisualKinds,
  hasRenderPlanContract,
  isApiPreparedMarkdown,
  shouldApplyClientMarkdownCompaction,
  stripRichUiRedundantProseFromMarkdown,
} from "../../chatPresentation";
import { fixtureToolCalls } from "../../message/testFixtures";

describe("presentationRenderHints", () => {
  it("não recompacta markdown quando a API enviou textRenderMode compact", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          stackPresentationPlan: {
            renderHints: { textRenderMode: "compact" },
          },
          tablePresentation: {
            type: "table",
            title: "Resultado",
            columns: [{ key: "a", label: "A" }],
            rows: [{ a: "1" }],
          },
        },
      },
    ]);
    const markdown = "### Resultado\n\n| A |\n| --- |\n| 1 |";

    expect(shouldApplyClientMarkdownCompaction(toolCalls)).toBe(false);
    expect(stripRichUiRedundantProseFromMarkdown(markdown, toolCalls)).toContain("| A |");
    expect(getPresentationRenderHintsFromToolCalls(toolCalls)?.textRenderMode).toBe("compact");
  });

  it("trata renderPlan v1 como markdown preparado pela API", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [{ kind: "markdown", slot: "lead", source: "textPresentation" }],
          },
          textPresentation: { markdown: "### Status\n\nResumo." },
        },
      },
    ]);

    expect(hasRenderPlanContract(toolCalls)).toBe(true);
    expect(isApiPreparedMarkdown(toolCalls)).toBe(true);
    expect(shouldApplyClientMarkdownCompaction(toolCalls)).toBe(false);
  });

  it("limita kinds visuais ao renderPlan v1", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
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
    ]);

    expect(getRenderPlanAllowedVisualKinds(toolCalls)).toEqual(new Set(["tree"]));
  });
});
