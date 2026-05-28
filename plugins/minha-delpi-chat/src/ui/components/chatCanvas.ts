import type { ChatCanvasOpenPayload, ChatMessageMetadata } from "../../data/api/chatTypes";

export function normalizeCanvasOpenPayload(
  raw: unknown,
): ChatCanvasOpenPayload | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }

  const record = raw as Record<string, unknown>;
  const markdown = String(record.markdown ?? "").trim();

  if (!markdown) {
    return null;
  }

  return {
    title: String(record.title ?? "Conteúdo do chat").trim() || "Conteúdo do chat",
    markdown,
    messageId:
      typeof record.messageId === "string" ? record.messageId : null,
    sourceMessageId:
      typeof record.sourceMessageId === "string"
        ? record.sourceMessageId
        : null,
  };
}

export function getCanvasOpenFromMetadata(
  metadata: ChatMessageMetadata | null | undefined,
): ChatCanvasOpenPayload | null {
  return normalizeCanvasOpenPayload(metadata?.canvasOpen);
}
