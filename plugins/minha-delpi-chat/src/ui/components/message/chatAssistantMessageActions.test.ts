import { describe, expect, it } from "vitest";

import type { ChatToolCall } from "../../../data/api/chatTypes";

import { buildAssistantMessageMenuActions } from "./chatAssistantMessageActions";

describe("buildAssistantMessageMenuActions", () => {
  it("não expõe troca de formato pós-resposta", () => {
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

    expect(actions).toEqual([]);
  });
});
