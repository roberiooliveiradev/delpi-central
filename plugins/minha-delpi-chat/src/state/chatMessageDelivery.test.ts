import { describe, expect, it } from "vitest";

import type { ChatMessage } from "../data/api/chatTypes";
import {
  isAssistantGenerating,
  sanitizeMessagesAfterStreamDismiss,
  sessionAwaitingAssistantResponse,
  shouldAppendPendingUserMessage,
} from "./chatMessageDelivery";
import { resolveUnansweredTurnRecovery } from "./chatTurnRecovery";

function userMessage(
  id: string,
  content: string,
  deliveryStatus?: string,
): ChatMessage {
  return {
    id,
    session_id: "sess-1",
    role: "user",
    content,
    created_at: "2026-05-30T12:00:00Z",
    metadata: deliveryStatus
      ? { delivery: { status: deliveryStatus } }
      : null,
  };
}

function assistantMessage(
  id: string,
  content: string,
  deliveryStatus: string,
): ChatMessage {
  return {
    id,
    session_id: "sess-1",
    role: "assistant",
    content,
    created_at: "2026-05-30T12:00:00Z",
    metadata: {
      delivery: { status: deliveryStatus, playbackPending: true },
    },
  };
}

describe("isAssistantGenerating", () => {
  it("identifica placeholder em geração", () => {
    expect(
      isAssistantGenerating(assistantMessage("asst-1", "", "generating")),
    ).toBe(true);
  });

  it("ignora mensagens prontas", () => {
    expect(
      isAssistantGenerating(assistantMessage("asst-1", "Pronta", "ready")),
    ).toBe(false);
  });
});

describe("sanitizeMessagesAfterStreamDismiss", () => {
  it("remove assistant generating ao cancelar stream", () => {
    const messages: ChatMessage[] = [
      userMessage("user-1", "360", "processing"),
      assistantMessage("asst-1", "", "generating"),
    ];

    const result = sanitizeMessagesAfterStreamDismiss(messages);

    expect(result).toHaveLength(1);
    expect(result[0]?.id).toBe("user-1");
    expect(result[0]?.metadata?.delivery).toEqual({
      status: "cancelled",
      playbackPending: false,
    });
  });

  it("remove assistant generating parcial com conteúdo", () => {
    const messages: ChatMessage[] = [
      userMessage("user-1", "360", "submitted"),
      assistantMessage("asst-1", "Resposta parcial...", "generating"),
    ];

    const result = sanitizeMessagesAfterStreamDismiss(messages);

    expect(result).toHaveLength(1);
    const delivery = result[0]?.metadata?.delivery as { status?: string } | undefined;
    expect(delivery?.status).toBe("cancelled");
  });

  it("não altera conversa já concluída", () => {
    const messages: ChatMessage[] = [
      userMessage("user-1", "Olá"),
      assistantMessage("asst-1", "Resposta final", "ready"),
    ];

    expect(sanitizeMessagesAfterStreamDismiss(messages)).toEqual(messages);
  });
});

describe("shouldAppendPendingUserMessage", () => {
  it("não duplica quando a pergunta já foi persistida com outro id", () => {
    expect(
      shouldAppendPendingUserMessage(
        [userMessage("user-1", "vvbbvb")],
        {
          ...userMessage("optimistic-1", "vvbbvb"),
          metadata: { optimistic: true },
        },
      ),
    ).toBe(false);
  });

  it("mantém placeholder enquanto a pergunta ainda não apareceu na lista", () => {
    expect(
      shouldAppendPendingUserMessage(
        [],
        userMessage("optimistic-1", "vvbbvb"),
      ),
    ).toBe(true);
  });
});

describe("sessionAwaitingAssistantResponse", () => {
  it("retorna true com assistant generating", () => {
    expect(
      sessionAwaitingAssistantResponse([
        userMessage("user-1", "360"),
        assistantMessage("asst-1", "", "generating"),
      ]),
    ).toBe(true);
  });

  it("retorna true com user in-flight", () => {
    expect(
      sessionAwaitingAssistantResponse([
        userMessage("user-1", "360", "processing"),
      ]),
    ).toBe(true);
  });

  it("retorna false após cancelamento local", () => {
    expect(
      sessionAwaitingAssistantResponse([
        userMessage("user-1", "360", "cancelled"),
      ]),
    ).toBe(false);
  });
});

describe("resolveUnansweredTurnRecovery", () => {
  it("não exibe recuperação após cancelamento explícito do usuário", () => {
    expect(
      resolveUnansweredTurnRecovery([
        userMessage("user-1", "me fale do produto 10080023", "cancelled"),
      ]),
    ).toBeNull();
  });

  it("oferece saída quando a última mensagem do usuário ficou órfã sem resposta", () => {
    expect(
      resolveUnansweredTurnRecovery([
        userMessage("user-1", "me fale do produto 10080023", "ready"),
      ]),
    ).toEqual({
      messageId: "user-1",
      retryContent: "me fale do produto 10080023",
      title: "Não consegui concluir a resposta.",
      message:
        "Não recebi resposta para esta pergunta. Tente de novo ou ative um agente com acesso aos dados.",
      reason: "orphaned",
    });
  });

  it("não exibe recuperação enquanto ainda aguarda resposta", () => {
    expect(
      resolveUnansweredTurnRecovery([
        userMessage("user-1", "oi", "processing"),
      ]),
    ).toBeNull();
  });

  it("respeita mensagem dispensada pelo usuário", () => {
    expect(
      resolveUnansweredTurnRecovery(
        [userMessage("user-1", "oi", "cancelled")],
        { dismissedMessageId: "user-1" },
      ),
    ).toBeNull();
  });
});
