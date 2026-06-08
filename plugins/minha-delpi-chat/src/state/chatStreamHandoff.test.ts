import { describe, expect, it } from "vitest";

import type { ChatMessage } from "../data/api/chatTypes";
import {
  applyStreamHandoffToMessages,
  shouldSkipPlaybackReveal,
  streamContentAlreadyDisplayed,
} from "./chatStreamHandoff";

function generatingAssistant(id: string): ChatMessage {
  return {
    id,
    session_id: "sess-1",
    role: "assistant",
    content: "",
    created_at: "2026-05-30T12:00:00Z",
    metadata: {
      delivery: { status: "generating", playbackPending: true },
    },
  };
}

describe("applyStreamHandoffToMessages", () => {
  it("substitui placeholder generating pela resposta pronta", () => {
    const messages: ChatMessage[] = [
      {
        id: "user-1",
        session_id: "sess-1",
        role: "user",
        content: "Olá",
        created_at: "2026-05-30T12:00:00Z",
        metadata: null,
      },
      generatingAssistant("asst-1"),
    ];

    const result = applyStreamHandoffToMessages(messages, {
      messageId: "asst-1",
      sessionId: "sess-1",
      answer: "Resposta final",
      sources: [],
      toolCalls: [],
    });

    expect(result).toHaveLength(2);
    expect(result[1]?.content).toBe("Resposta final");
    expect(result[1]?.metadata?.delivery).toEqual({
      status: "ready",
      playbackPending: false,
    });
  });
});

describe("streamContentAlreadyDisplayed", () => {
  it("retorna true quando o texto do stream já coincide com o payload", () => {
    expect(
      streamContentAlreadyDisplayed("Mesma resposta", [], {
        answer: "Mesma resposta",
        toolCalls: [],
      }),
    ).toBe(true);
  });

  it("retorna false quando o stream ainda não tem o texto final", () => {
    expect(
      streamContentAlreadyDisplayed("Parcial", [], {
        answer: "Resposta completa",
        toolCalls: [],
      }),
    ).toBe(false);
  });

  it("ignora playback incremental quando a API não enviou tokens", () => {
    expect(
      shouldSkipPlaybackReveal("", [], {
        answer: "Olá! O que vamos resolver hoje?",
        toolCalls: [],
      }),
    ).toBe(true);

    expect(
      streamContentAlreadyDisplayed("", [], {
        answer: "Olá! O que vamos resolver hoje?",
        toolCalls: [],
      }),
    ).toBe(true);
  });
});
