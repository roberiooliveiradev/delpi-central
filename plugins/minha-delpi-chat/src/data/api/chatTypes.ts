export type ChatSession = {
  id: string;
  title: string | null;
  context: string | null;
  project_id: string | null;
  agent_key: string | null;
  is_pinned: boolean;
  pinned_at: string | null;
  archived_at: string | null;
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
  projectId?: string | null;
  agentKey?: string | null;
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

export type ChatArtifact = {
  id: string;
  session_id: string;
  message_id: string | null;
  user_id: string;
  type: "markdown" | "table" | "json" | "report" | string;
  title: string;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type CreateChatArtifactPayload = {
  type: "markdown" | "table" | "json" | "report" | string;
  title: string;
  content: string;
  messageId?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type UpdateChatArtifactPayload = {
  title?: string;
  content?: string;
  metadata?: Record<string, unknown> | null;
};

export type ChatAgent = {
  id: string;
  key: string;
  name: string;
  description: string | null;
  enabled: boolean;
  metadata: Record<string, unknown> | null;
  owner_user_id: string | null;
  visibility: "system" | "private" | "public" | string;
  category: string | null;
  icon: string | null;
  response_style: string | null;
  max_tool_calls: number;
  requires_confirmation_for_write: boolean;
  access_role: "system" | "owner" | "editor" | "viewer" | string;
  created_at: string;
  updated_at: string;
};

export type ChatProject = {
  id: string;
  name: string;
  description: string | null;
  instructions: string | null;
  default_agent_key: string | null;
  visibility: "private" | "public" | string;
  icon: string | null;
  color: string | null;
  archived_at: string | null;
  metadata: Record<string, unknown> | null;
  access_role: "owner" | "editor" | "viewer" | string;
  created_at: string;
  updated_at: string;
};

export type CreateChatProjectPayload = {
  name: string;
  description?: string | null;
  instructions?: string | null;
  defaultAgentKey?: string | null;
  visibility?: "private" | "public" | string;
  icon?: string | null;
  color?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type UpdateChatProjectPayload = {
  name?: string;
  description?: string | null;
  instructions?: string | null;
  defaultAgentKey?: string | null;
  visibility?: "private" | "public" | string;
  icon?: string | null;
  color?: string | null;
  metadata?: Record<string, unknown> | null;
  archived?: boolean;
};

export type CreateChatAgentPayload = {
  key?: string | null;
  name: string;
  description?: string | null;
  systemPrompt?: string | null;
  visibility?: "private" | "public" | string;
  category?: string | null;
  icon?: string | null;
  responseStyle?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type UpdateChatAgentPayload = {
  name?: string;
  description?: string | null;
  systemPrompt?: string | null;
  visibility?: "private" | "public" | string;
  category?: string | null;
  icon?: string | null;
  responseStyle?: string | null;
  metadata?: Record<string, unknown> | null;
  enabled?: boolean;
};

export type ShareChatAgentPayload = {
  targetUserId: string;
  role: "viewer" | "editor" | string;
};

export type UpsertChatAgentActionPayload = {
  providerKey: string;
  actionId: string;
  sensitivity?: "read" | "write" | "admin" | string;
  requiresConfirmation?: boolean;
  enabled?: boolean;
};


export type ShareChatProjectPayload = {
  targetUserId: string;
  role: "viewer" | "editor" | string;
};
