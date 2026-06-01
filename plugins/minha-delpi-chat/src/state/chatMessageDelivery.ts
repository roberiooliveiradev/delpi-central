import type { ChatMessage } from "../data/api/chatTypes";

export function getDeliveryStatus(
  metadata: ChatMessage["metadata"],
): string | null {
  const delivery = metadata?.delivery;

  if (!delivery || typeof delivery !== "object") {
    return null;
  }

  const status = (delivery as { status?: unknown }).status;

  return typeof status === "string" ? status : null;
}

export function isAssistantGenerating(message: ChatMessage): boolean {
  return message.role === "assistant" && getDeliveryStatus(message.metadata) === "generating";
}

function isInFlightUserDelivery(status: string | null): boolean {
  return status === "submitted" || status === "processing";
}

function patchMessageDeliveryStatus(
  message: ChatMessage,
  status: string,
): ChatMessage {
  const delivery = (message.metadata?.delivery as Record<string, unknown> | undefined) ?? {};

  return {
    ...message,
    metadata: {
      ...(message.metadata ?? {}),
      delivery: {
        ...delivery,
        status,
        playbackPending: false,
      },
    },
  };
}

export function sanitizeMessagesAfterStreamDismiss(
  messages: ChatMessage[],
): ChatMessage[] {
  let list = [...messages];

  while (list.length > 0) {
    const last = list[list.length - 1];

    if (last.role === "assistant" && isAssistantGenerating(last)) {
      list = list.slice(0, -1);
      continue;
    }

    break;
  }

  if (!list.length) {
    return list;
  }

  const lastIndex = list.length - 1;
  const last = list[lastIndex];

  if (last.role === "assistant" && isAssistantGenerating(last)) {
    return list.map((message, index) =>
      index === lastIndex ? patchMessageDeliveryStatus(message, "ready") : message,
    );
  }

  if (last.role !== "user" || !isInFlightUserDelivery(getDeliveryStatus(last.metadata))) {
    return list;
  }

  return list.map((message, index) => {
    if (index !== lastIndex) {
      return message;
    }

    return patchMessageDeliveryStatus(message, "cancelled");
  });
}

export function shouldAppendPendingUserMessage(
  messages: ChatMessage[],
  pendingUserMessage: ChatMessage,
): boolean {
  if (messages.some((message) => message.id === pendingUserMessage.id)) {
    return false;
  }

  const pendingContent = pendingUserMessage.content.trim();

  if (!pendingContent) {
    return true;
  }

  const lastUserMessage = [...messages]
    .reverse()
    .find((message) => message.role === "user");

  if (lastUserMessage && lastUserMessage.content.trim() === pendingContent) {
    return false;
  }

  return true;
}

export function sessionAwaitingAssistantResponse(messages: ChatMessage[]): boolean {
  if (!messages.length) {
    return false;
  }

  const last = messages[messages.length - 1];

  if (isAssistantGenerating(last)) {
    return true;
  }

  if (last.role !== "user") {
    return false;
  }

  const deliveryStatus = getDeliveryStatus(last.metadata);

  return isInFlightUserDelivery(deliveryStatus);
}
