import type { ChatMessage } from "../data/api/chatTypes";

export type ContextItemPayload = {
  content: string;
  filename?: string;
  role?: "user" | "assistant";
  messageId?: string;
  kind?: "question" | "answer";
  question?: string;
  answer?: string;
  questionMessageId?: string;
  answerMessageId?: string;
};

export type ConversationContextPick = {
  id: string;
  role: "user" | "assistant";
  preview: string;
  content: string;
};

const MAX_CONTEXT_MESSAGE_CHARS = 12_000;
const MAX_PREVIEW_CHARS = 88;

export function messageTextForContext(message: ChatMessage): string {
  const raw = String(message.content || "").trim();

  if (raw) {
    return raw.slice(0, MAX_CONTEXT_MESSAGE_CHARS);
  }

  const playback = message.metadata?.playback;

  if (playback && typeof playback === "object" && "text" in playback) {
    return String((playback as { text?: string }).text || "")
      .trim()
      .slice(0, MAX_CONTEXT_MESSAGE_CHARS);
  }

  return "";
}

export function previewConversationText(text: string): string {
  const normalized = text.replace(/\s+/g, " ").trim();

  if (!normalized) {
    return "(vazio)";
  }

  if (normalized.length <= MAX_PREVIEW_CHARS) {
    return normalized;
  }

  return `${normalized.slice(0, MAX_PREVIEW_CHARS - 1)}…`;
}

export function buildContextPayloadFromMessage(message: ChatMessage): ContextItemPayload | null {
  const content = messageTextForContext(message);

  if (!content) {
    return null;
  }

  const role = message.role === "assistant" ? "assistant" : "user";

  return {
    content,
    role,
    messageId: message.id,
    kind: role === "assistant" ? "answer" : "question",
  };
}

export function buildContextTurnPayload(
  questionMessage: ChatMessage,
  answerMessage: ChatMessage,
): ContextItemPayload | null {
  const question = messageTextForContext(questionMessage);
  const answer = messageTextForContext(answerMessage);

  if (!question || !answer) {
    return null;
  }

  return {
    content: "",
    question,
    answer,
    questionMessageId: questionMessage.id,
    answerMessageId: answerMessage.id,
  };
}

export function findPreviousUserMessage(
  messages: ChatMessage[],
  beforeMessageId: string,
): ChatMessage | null {
  const index = messages.findIndex((message) => message.id === beforeMessageId);

  if (index <= 0) {
    return null;
  }

  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    const candidate = messages[cursor];

    if (candidate.role === "user" && messageTextForContext(candidate)) {
      return candidate;
    }
  }

  return null;
}

function hashContextFingerprint(text: string): string {
  let hash = 0;

  for (let index = 0; index < text.length; index += 1) {
    hash = (hash * 31 + text.charCodeAt(index)) | 0;
  }

  return String(hash);
}

/** Chave estável para evitar duplicar o mesmo contexto (UI + alinhado ao backend). */
export function contextPayloadDedupKey(payload: ContextItemPayload): string | null {
  const messageId = String(payload.messageId || "").trim();
  const kind = String(payload.kind || "").trim().toLowerCase();

  if (messageId && (kind === "question" || kind === "answer")) {
    return `msg:${messageId}:${kind}`;
  }

  const questionMessageId = String(payload.questionMessageId || "").trim();
  const answerMessageId = String(payload.answerMessageId || "").trim();

  if (questionMessageId && answerMessageId) {
    return `turn:${questionMessageId}:${answerMessageId}`;
  }

  const content = String(payload.content || payload.question || payload.answer || "")
    .trim()
    .slice(0, 500);
  const filename = String(payload.filename || "").trim();

  if (!content && !filename) {
    return null;
  }

  return `content:${hashContextFingerprint(`${kind || "note"}:${filename}:${content}`)}`;
}

export function listRecentConversationPicks(
  messages: ChatMessage[],
  maxItems = 8,
): ConversationContextPick[] {
  const picks: ConversationContextPick[] = [];

  for (let index = messages.length - 1; index >= 0 && picks.length < maxItems; index -= 1) {
    const message = messages[index];

    if (message.role !== "user" && message.role !== "assistant") {
      continue;
    }

    const content = messageTextForContext(message);

    if (!content) {
      continue;
    }

    picks.push({
      id: message.id,
      role: message.role === "assistant" ? "assistant" : "user",
      content,
      preview: previewConversationText(content),
    });
  }

  return picks;
}
