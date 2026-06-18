export const CHAT_SESSION_DRAG_MIME = "application/x-delpi-chat-session-id";

export function setChatSessionDragData(dataTransfer: DataTransfer, sessionId: string) {
  dataTransfer.setData(CHAT_SESSION_DRAG_MIME, sessionId);
  dataTransfer.setData("text/plain", sessionId);
  dataTransfer.effectAllowed = "move";
}

export function readChatSessionDragId(dataTransfer: DataTransfer): string | null {
  const sessionId = dataTransfer.getData(CHAT_SESSION_DRAG_MIME);

  if (sessionId.trim()) {
    return sessionId;
  }

  const fallback = dataTransfer.getData("text/plain").trim();

  return fallback || null;
}

export function isChatSessionDragEvent(dataTransfer: DataTransfer): boolean {
  return (
    dataTransfer.types.includes(CHAT_SESSION_DRAG_MIME) ||
    dataTransfer.types.includes("text/plain")
  );
}
