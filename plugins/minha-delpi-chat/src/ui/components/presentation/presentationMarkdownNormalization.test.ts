import { describe, expect, it } from "vitest";

import type { ChatToolCall } from "../../../data/api/chatTypes";
import {
  getTextMarkdownFromToolCalls,
  isLlmProseDecoupledFromToolCalls,
  resolveLeadMarkdownSource,
} from "./presentationMarkdownNormalization";

describe("presentationMarkdownNormalization prose delivery", () => {
  const decoupledToolCalls: ChatToolCall[] = [
    {
      name: "execute_external_action",
      metadata: {
        ok: true,
        llmProseDecoupled: true,
        proseDeliveryMode: "llm",
        textPresentation: {
          type: "markdown",
          markdown: "### Template\n\nNão deve aparecer.",
        },
        presentationDecision: { proseSource: "llm", layoutMode: "stack" },
      },
    },
  ];

  it("ignora markdown do metadata quando decoupled", () => {
    expect(isLlmProseDecoupledFromToolCalls(decoupledToolCalls)).toBe(true);
    expect(getTextMarkdownFromToolCalls(decoupledToolCalls)).toBe("");
  });

  it("resolve lead source como assistantMessage quando decoupled", () => {
    const metadata = decoupledToolCalls[0].metadata as Record<string, unknown>;

    expect(resolveLeadMarkdownSource(metadata, "Resposta do LLM.")).toBe(
      "assistantMessage",
    );
  });
});
