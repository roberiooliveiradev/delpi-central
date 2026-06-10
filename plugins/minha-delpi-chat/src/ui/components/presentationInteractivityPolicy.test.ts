import { describe, expect, it } from "vitest";

import type { ChatToolCall } from "../../data/api/chatTypes";

import { buildFormatSwitchActionsFromToolCalls } from "./presentationInteractivityPolicy";

describe("buildFormatSwitchActionsFromToolCalls", () => {
  it("expõe chip de gráfico quando chart está em availableViews e não selecionado", () => {
    const toolCalls: ChatToolCall[] = [
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
    ];

    const labels = buildFormatSwitchActionsFromToolCalls(toolCalls).map((action) => action.label);

    expect(labels).toContain("Ver em gráfico");
    expect(labels).toContain("Ver como tabela");
    expect(labels).not.toContain("Ver em texto");
  });

  it("omite chip de gráfico quando já está selecionado", () => {
    const toolCalls: ChatToolCall[] = [
      {
        name: "execute_external_action",
        metadata: {
          presentationDecision: {
            selected: "chart",
            availableViews: ["text", "table", "chart"],
            visualOrder: ["text", "table", "chart"],
          },
        },
      },
    ];

    const labels = buildFormatSwitchActionsFromToolCalls(toolCalls).map((action) => action.label);

    expect(labels).not.toContain("Ver em gráfico");
    expect(labels).toContain("Ver como tabela");
  });
});
