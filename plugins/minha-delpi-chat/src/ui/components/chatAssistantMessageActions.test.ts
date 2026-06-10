import { describe, expect, it } from "vitest";

import type { ChatToolCall } from "../../data/api/chatTypes";

import { buildAssistantMessageMenuActions } from "./chatAssistantMessageActions";

describe("buildAssistantMessageMenuActions", () => {
  it("expõe ações de formato a partir de presentationDecision", () => {
    const actions = buildAssistantMessageMenuActions([
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            selected: "text",
            availableViews: ["text", "table", "chart"],
            visualOrder: ["text", "table", "chart"],
          },
        },
      },
    ] as ChatToolCall[]);

    const labels = actions.map((action) => action.label);

    expect(labels).toContain("Ver como tabela");
    expect(labels).toContain("Ver em gráfico");
    expect(labels).toContain("Colocar na lousa");
  });
});
