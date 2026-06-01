import { describe, expect, it } from "vitest";

import { buildAssistantMessageMenuActions } from "./chatAssistantMessageActions";

describe("buildAssistantMessageMenuActions", () => {
  it("expõe ações de formato quando há availableFormats", () => {
    const actions = buildAssistantMessageMenuActions([
      {
        name: "execute_external_action",
        metadata: {
          availableFormats: ["text", "table", "chart"],
        },
      },
    ]);

    const labels = actions.map((action) => action.label);

    expect(labels).toContain("Ver em tabela");
    expect(labels).toContain("Ver em gráfico");
    expect(labels).toContain("Colocar na lousa");
  });
});
