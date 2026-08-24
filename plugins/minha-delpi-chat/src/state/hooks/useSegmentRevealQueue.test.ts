import { describe, expect, it } from "vitest";

import type { ChatToolCall } from "../../data/api/chatTypes";
import { buildAssistantContentSegments } from "../../ui/components/message/assistantContentSegments";

describe("segment reveal helpers", () => {
  it("monta segmentos na ordem do renderPlan para estoque", () => {
    const toolCalls = [
      {
        name: "execute_external_action",
        arguments: { actionId: "stock" },
        metadata: {
          ok: true,
          compositionRole: "primary",
          presentationDecision: { selected: "table" },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [
              { kind: "markdown", slot: "lead" },
              { kind: "table", slot: "primary" },
            ],
          },
          tablePresentations: [
            {
              type: "table",
              title: "Estoque",
              columns: [{ key: "a", label: "A" }],
              rows: [{ a: "1" }],
            },
          ],
        },
      },
    ] as unknown as ChatToolCall[];

    const segments = buildAssistantContentSegments("Resumo do estoque", toolCalls);
    const kinds = segments.map((segment) => segment.kind);

    expect(kinds).toContain("markdown");
    expect(kinds).toContain("table");
    expect(kinds.indexOf("markdown")).toBeLessThan(kinds.indexOf("table"));
  });
});
