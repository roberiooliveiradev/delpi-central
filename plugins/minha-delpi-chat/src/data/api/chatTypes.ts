export type ChatSession = {
  id: string;
  title: string | null;
  context: string | null;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system" | string;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export type CreateChatSessionPayload = {
  title?: string;
  context?: string;
};

export type SendChatMessagePayload = {
  message: string;
  context?: string;
};

export type SendChatMessageResponse = {
  messageId: string;
  answer: string;
  sources: unknown[];
  toolCalls: unknown[];
};
