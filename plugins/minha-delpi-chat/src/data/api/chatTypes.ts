export type ChatSession = {
  id: string;
  title: string | null;
  context: string | null;
  created_at: string;
  updated_at: string;
};

export type ChatSource = {
  id?: string;
  documentId?: string;
  title?: string | null;
  sourceType?: string | null;
  sourceRef?: string | null;
  chunkIndex?: number | null;
  score?: number | null;
};

export type ChatPresentation =
  | {
      type: "table";
      title: string;
      columns: { key: string; label: string }[];
      rows: Record<string, unknown>[];
    }
  | {
      type: "json";
      title: string;
      data: unknown;
    };

export type ChatToolCall = {
  name?: string;
  arguments?: Record<string, unknown>;
  reason?: string | null;
  metadata?: (Record<string, unknown> & {
    presentation?: ChatPresentation | null;
  }) | null;
};

export type ChatMessageMetadata = {
  sources?: ChatSource[];
  toolCalls?: ChatToolCall[];
  rag?: {
    enabled?: boolean;
    sourceCount?: number;
    sources?: ChatSource[];
  };
  [key: string]: unknown;
};

export type ChatMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system" | string;
  content: string;
  metadata: ChatMessageMetadata | null;
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
  sources: ChatSource[];
  toolCalls: ChatToolCall[];
};
