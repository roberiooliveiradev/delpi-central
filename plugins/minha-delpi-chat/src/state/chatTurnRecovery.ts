import recoveryContent from "../content/chat_turn_recovery.json";

import type { ChatMessage } from "../data/api/chatTypes";
import {
  getDeliveryStatus,
  sessionAwaitingAssistantResponse,
} from "./chatMessageDelivery";

export const CHAT_TURN_STALL_TIMEOUT_MS = 120_000;

export type UnansweredTurnReason = "cancelled" | "timeout" | "orphaned";

export type UnansweredTurnRecovery = {
  messageId: string;
  retryContent: string;
  title: string;
  message: string;
  reason: UnansweredTurnReason;
};

function recoveryMessage(reason: UnansweredTurnReason): string {
  return (
    recoveryContent.messages[reason] ||
    recoveryContent.messages.orphaned
  );
}

function resolveUnansweredReason(message: ChatMessage): UnansweredTurnReason {
  const delivery = (message.metadata?.delivery as Record<string, unknown> | undefined) ?? {};
  const status = getDeliveryStatus(message.metadata);

  if (status === "cancelled") {
    return "cancelled";
  }

  if (typeof delivery.error === "string" && delivery.error.trim()) {
    return "orphaned";
  }

  return "orphaned";
}

export function resolveUnansweredTurnRecovery(
  messages: ChatMessage[],
  options?: {
    dismissedMessageId?: string | null;
    forcedReason?: UnansweredTurnReason;
  },
): UnansweredTurnRecovery | null {
  if (!messages.length || sessionAwaitingAssistantResponse(messages)) {
    return null;
  }

  const last = messages[messages.length - 1];

  if (last.role !== "user") {
    return null;
  }

  if (last.metadata?.optimistic === true || String(last.id).startsWith("optimistic-")) {
    return null;
  }

  if (options?.dismissedMessageId && last.id === options.dismissedMessageId) {
    return null;
  }

  const deliveryStatus = getDeliveryStatus(last.metadata);

  // Cancelamento explícito (botão Parar) não é falha — o rascunho já volta ao composer.
  if (deliveryStatus === "cancelled") {
    return null;
  }

  const retryContent = String(last.content || "").trim();

  if (!retryContent) {
    return null;
  }

  const reason = options?.forcedReason ?? resolveUnansweredReason(last);

  return {
    messageId: last.id,
    retryContent,
    title: recoveryContent.title,
    message: recoveryMessage(reason),
    reason,
  };
}

export function stallTimeoutMessage(): string {
  return recoveryMessage("timeout");
}
