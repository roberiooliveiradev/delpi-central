import { describe, expect, it } from "vitest";

import {
  getPresentationRenderHintsFromToolCalls,
  shouldApplyClientMarkdownCompaction,
  stripRichUiRedundantProseFromMarkdown,
} from "./chatPresentation";
import { fixtureToolCalls } from "./testFixtures";

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
});
