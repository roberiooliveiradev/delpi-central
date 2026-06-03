import { describe, expect, it } from "vitest";

import { contextPayloadDedupKey } from "./chatContextFromMessage";

describe("contextPayloadDedupKey", () => {
  it("usa messageId + kind para pergunta da conversa", () => {
    expect(
      contextPayloadDedupKey({
        content: "Monte uma consulta SA1",
        messageId: "msg-1",
        kind: "question",
      }),
    ).toBe("msg:msg-1:question");
  });

  it("usa par de mensagens para turno completo", () => {
    expect(
      contextPayloadDedupKey({
        content: "",
        question: "Pergunta",
        answer: "Resposta",
        questionMessageId: "u1",
        answerMessageId: "a1",
      }),
    ).toBe("turn:u1:a1");
  });
});
