import type { ChatCanvasOpenPayload, ChatMessageMetadata } from "../../../data/api/chatTypes";

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

  const version = record.version;
  const documentType = record.documentType;

  return {
    title: String(record.title ?? "Conteúdo do chat").trim() || "Conteúdo do chat",
    markdown,
    messageId:
      typeof record.messageId === "string" ? record.messageId : null,
    sourceMessageId:
      typeof record.sourceMessageId === "string"
        ? record.sourceMessageId
        : null,
    version: typeof version === "number" ? version : null,
    documentType: typeof documentType === "string" ? documentType : null,
  };
}

export function enrichCanvasOpenFromSessionMetadata(
  payload: ChatCanvasOpenPayload,
  metadata: ChatMessageMetadata | null | undefined,
): ChatCanvasOpenPayload {
  const canvas = metadata?.canvas;

  if (!canvas || typeof canvas !== "object") {
    return payload;
  }

  const record = canvas as Record<string, unknown>;

  return {
    ...payload,
    version:
      typeof record.version === "number"
        ? record.version
        : payload.version ?? null,
    documentType:
      typeof record.documentType === "string"
        ? record.documentType
        : payload.documentType ?? null,
  };
}

export function getCanvasOpenFromMetadata(
  metadata: ChatMessageMetadata | null | undefined,
): ChatCanvasOpenPayload | null {
  return normalizeCanvasOpenPayload(metadata?.canvasOpen);
}
