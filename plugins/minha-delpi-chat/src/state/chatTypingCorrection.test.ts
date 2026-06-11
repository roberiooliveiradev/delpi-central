import { describe, expect, it } from "vitest";

import {
  buildTypingCorrectionMetadata,
  dismissTypingSuggestion,
  isTypingSuggestionDismissed,
  shouldClearTypingSuggestion,
} from "./chatTypingCorrection";

import type { ChatTypingSuggestion } from "../data/api/chatTypes";

describe("chatTypingCorrection", () => {
  it("registra dismiss por sessão (T6)", () => {
    const sessionId = "session-test";
    const original = "estouque do produto 90262404";

    dismissTypingSuggestion(sessionId, original);

    expect(isTypingSuggestionDismissed(sessionId, original)).toBe(true);
    expect(isTypingSuggestionDismissed("other-session", original)).toBe(false);
  });

  it("monta metadata aceita para envio", () => {
    const suggestion: ChatTypingSuggestion = {
      original: "estouque",
      corrected: "estoque",
      changes: [
        {
          offset: 0,
          length: 8,
          replacement: "estoque",
          from: "estouque",
          to: "estoque",
          kind: "typo_rule",
        },
      ],
    };

    expect(buildTypingCorrectionMetadata(suggestion, true)).toEqual({
      original: "estouque",
      corrected: "estoque",
      accepted: true,
      source: "domain_dictionary",
      changes: [{ from: "estouque", to: "estoque", kind: "typo_rule" }],
    });
  });

  it("limpa sugestão quando o draft muda", () => {
    expect(shouldClearTypingSuggestion("estouque", "estouque do produto")).toBe(true);
    expect(shouldClearTypingSuggestion("estouque", "estouque")).toBe(false);
  });
});
