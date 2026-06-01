import { describe, expect, it } from "vitest";

import { computeToolsSummary } from "./toolsSummary";

describe("computeToolsSummary", () => {
  it("resume LLM, saúde e contagens de actions", () => {
    expect(
      computeToolsSummary(
        { provider: "ollama", model: "qwen", temperature: 0.2, maxTokens: 4096 },
        { status: "ok", items: [] },
        4,
        12,
      ),
    ).toEqual({
      llmConfigured: true,
      llmLabel: "ollama · qwen",
      healthLabel: "Operacional",
      globalActions: 4,
      chatActions: 12,
    });
  });
});
