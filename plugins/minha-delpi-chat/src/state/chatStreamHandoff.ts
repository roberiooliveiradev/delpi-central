import type { ChatMessage, ChatSource, ChatToolCall } from "../data/api/chatTypes";
import { isAssistantGenerating } from "./chatMessageDelivery";
import type { ChatPlaybackPayload } from "./hooks/useChatMessagePlayback";

export type AssistantTurnHandoff = {
  messageId: string;
  sessionId: string;
  answer: string;
  sources: ChatSource[];
  toolCalls: ChatToolCall[];
  adminDebug?: Record<string, unknown> | null;
};

function buildReadyAssistantMetadata(
  handoff: AssistantTurnHandoff,
  existing: ChatMessage["metadata"] | null | undefined,
): ChatMessage["metadata"] {
  const delivery = (existing?.delivery as Record<string, unknown> | undefined) ?? {};

  return {
    ...(existing ?? {}),
    sources: handoff.sources.length > 0 ? handoff.sources : existing?.sources,
    toolCalls:
      handoff.toolCalls.length > 0 ? handoff.toolCalls : existing?.toolCalls,
    ...(handoff.adminDebug ? { adminDebug: handoff.adminDebug } : {}),
    delivery: {
      ...delivery,
      status: "ready",
      playbackPending: false,
    },
  };
}

export function applyStreamHandoffToMessages(
  messages: ChatMessage[],
  handoff: AssistantTurnHandoff,
): ChatMessage[] {
  let list = [...messages];

  while (list.length > 0) {
    const last = list[list.length - 1];

    if (
      last.role === "assistant" &&
      isAssistantGenerating(last) &&
      !String(last.content ?? "").trim()
    ) {
      list = list.slice(0, -1);
      continue;
    }

    break;
  }

  const existingIndex = list.findIndex((message) => message.id === handoff.messageId);

  if (existingIndex >= 0) {
    return list.map((message, index) => {
      if (index !== existingIndex) {
        return message;
      }

      return {
        ...message,
        content: handoff.answer || message.content,
        metadata: buildReadyAssistantMetadata(handoff, message.metadata),
      };
    });
  }

  const readyMessage: ChatMessage = {
    id: handoff.messageId,
    session_id: handoff.sessionId,
    role: "assistant",
    content: handoff.answer,
    created_at: new Date().toISOString(),
    metadata: buildReadyAssistantMetadata(handoff, null),
  };

  if (list.length > 0) {
    const last = list[list.length - 1];

    if (last.role === "assistant" && isAssistantGenerating(last)) {
      return [
        ...list.slice(0, -1),
        {
          ...readyMessage,
          created_at: last.created_at,
          session_id: last.session_id || handoff.sessionId,
          parent_message_id: last.parent_message_id,
        },
      ];
    }
  }

  return [...list, readyMessage];
}

export function streamContentAlreadyDisplayed(
  streamingAnswer: string,
  streamingToolCalls: ChatToolCall[],
  payload: Pick<ChatPlaybackPayload, "answer" | "toolCalls" | "skipReveal">,
): boolean {
  if (shouldSkipPlaybackReveal(streamingAnswer, streamingToolCalls, payload)) {
    return true;
  }

  const streamed = String(streamingAnswer ?? "").trim();
  const finalAnswer = String(payload.answer ?? "").trim();

  if (!streamed || streamed !== finalAnswer) {
    return false;
  }

  const payloadToolCalls = payload.toolCalls ?? [];

  if (payloadToolCalls.length === 0) {
    return true;
  }

  if (streamingToolCalls.length === 0) {
    return false;
  }

  return payloadToolCalls.length === streamingToolCalls.length;
}

/**
 * Evita reanimar playback quando a API montou a resposta sem tokens SSE
 * (ex.: small talk / direct answer com persist_before_playback).
 */
export function shouldSkipPlaybackReveal(
  streamingAnswer: string,
  streamingToolCalls: ChatToolCall[],
  payload: Pick<ChatPlaybackPayload, "answer" | "toolCalls" | "skipReveal">,
): boolean {
  if (payload.skipReveal) {
    return true;
  }

  const streamed = String(streamingAnswer ?? "").trim();
  const finalAnswer = String(payload.answer ?? "").trim();

  if (!streamed && finalAnswer) {
    return true;
  }

  if (!streamed || streamed !== finalAnswer) {
    return false;
  }

  const payloadToolCalls = payload.toolCalls ?? [];

  if (payloadToolCalls.length === 0) {
    return true;
  }

  if (streamingToolCalls.length === 0) {
    return false;
  }

  return payloadToolCalls.length === streamingToolCalls.length;
}

export function handoffFromPlaybackPayload(
  sessionId: string,
  payload: ChatPlaybackPayload,
): AssistantTurnHandoff {
  return {
    messageId: payload.messageId,
    sessionId,
    answer: payload.answer,
    sources: payload.sources,
    toolCalls: payload.toolCalls,
    adminDebug: payload.adminDebug ?? null,
  };
}
