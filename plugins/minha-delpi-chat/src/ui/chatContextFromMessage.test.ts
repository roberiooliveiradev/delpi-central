import { describe, expect, it } from "vitest";

import {
  buildContextPayloadFromMessage,
  buildContextTurnPayload,
  findPreviousUserMessage,
  messageTextForContext,
} from "./chatContextFromMessage";
import type { ChatMessage } from "../data/api/chatTypes";

function msg(partial: Partial<ChatMessage> & Pick<ChatMessage, "id" | "role">): ChatMessage {
  return {
    content: "",
    created_at: "2026-01-01T00:00:00Z",
    session_id: "s1",
    ...partial,
  };
}

describe("chatContextFromMessage", () => {
  it("monta payload de pergunta", () => {
    const payload = buildContextPayloadFromMessage(
      msg({ id: "u1", role: "user", content: "Qual o estoque?" }),
    );

    expect(payload?.kind).toBe("question");
    expect(payload?.role).toBe("user");
  });

  it("monta par pergunta+resposta", () => {
    const messages = [
      msg({ id: "u1", role: "user", content: "Compare A e B" }),
      msg({ id: "a1", role: "assistant", content: "A difere em prazo." }),
    ];

    const payload = buildContextTurnPayload(messages[0], messages[1]);

    expect(payload?.question).toContain("Compare");
    expect(payload?.answer).toContain("difer");
  });

  it("encontra pergunta anterior à resposta", () => {
    const messages = [
      msg({ id: "u1", role: "user", content: "Pergunta 1" }),
      msg({ id: "a1", role: "assistant", content: "Resposta 1" }),
    ];

    expect(findPreviousUserMessage(messages, "a1")?.id).toBe("u1");
  });

  it("usa playback quando content vazio", () => {
    const text = messageTextForContext(
      msg({
        id: "a1",
        role: "assistant",
        content: "",
        metadata: { playback: { text: "Texto do playback" } },
      }),
    );

    expect(text).toContain("playback");
  });
});
