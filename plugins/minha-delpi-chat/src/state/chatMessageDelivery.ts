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

export function sessionAwaitingAssistantResponse(messages: ChatMessage[]): boolean {
  if (!messages.length) {
    return false;
  }

  const last = messages[messages.length - 1];

  if (isAssistantGenerating(last)) {
    return true;
  }

  return last.role === "user";
}
