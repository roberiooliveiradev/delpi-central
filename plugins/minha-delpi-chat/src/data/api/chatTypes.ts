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
  scope?: string | null;
  agentKey?: string | null;
  projectId?: string | null;
  sessionId?: string | null;
  attachmentId?: string | null;
};

export type ChatKpiCard = {
  label: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "stable";
  delta?: string;
  color?: string;
};

export type ChatPresentation =
  | {
      type: "table";
      title: string;
      columns: {
        key: string;
        label: string;
        dataType?: "text" | "number" | "currency" | "date" | "percent" | "quantity";
      }[];
      rows: Record<string, unknown>[];
    }
  | {
      type: "chart";
      title: string;
      chartType: "bar" | "line" | "pie" | "area";
      data: Record<string, unknown>[];
      config?: {
        xAxis?: string;
        yAxis?: string | string[];
        colors?: string[];
        legend?: boolean;
      };
    }
  | {
      type: "kpi";
      title: string;
      cards: ChatKpiCard[];
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
    responsePreview?: string | null;
    actionId?: string | null;
    provider?: string | null;
    method?: string | null;
    path?: string | null;
    statusCode?: number | null;
    ok?: boolean | null;
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
  user_feedback?: -1 | 1 | null;
};

export type ChatMessageFeedbackResponse = {
  messageId: string;
  userId: string;
  rating: -1 | 1;
  createdAt: string;
  updatedAt: string;
} | {
  removed: boolean;
};

export type CreateChatSessionPayload = {
  title?: string;
  context?: string;
  projectId?: string | null;
  agentKey?: string | null;
};

export type ChatAttachment = {
  id: string;
  session_id: string;
  message_id: string | null;
  project_id: string | null;
  agent_key: string | null;
  filename: string;
  original_filename: string;
  content_type: string | null;
  size_bytes: number;
  status: "uploaded" | "indexed" | "unsupported" | "index_failed" | string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type SendChatMessagePayload = {
  message: string;
  context?: string;
  attachmentIds?: string[];
  agentKey?: string | null;
};

export type ChatCanvasOpenPayload = {
  title: string;
  markdown: string;
  messageId?: string | null;
  sourceMessageId?: string | null;
};

export type SendChatMessageResponse = {
  messageId: string;
  answer: string;
  sources: ChatSource[];
  toolCalls: ChatToolCall[];
  playback?: boolean;
  canvasOpen?: ChatCanvasOpenPayload | null;
};

export type ChatPlaybackEvent = {
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
  system_prompt?: string | null;
  created_at: string;
  updated_at: string;
  sessions_in_window?: number | null;
  total_sessions?: number | null;
  published_version?: number;
  published_at?: string | null;
  has_unpublished_changes?: boolean;
};

export type ChatAgentVersion = {
  id: string;
  version: number;
  event: string;
  createdAt: string | null;
  createdBy: string | null;
};

export type ChatAgentPreviewDraft = {
  key?: string | null;
  name: string;
  description?: string | null;
  systemPrompt?: string | null;
  responseStyle?: string | null;
  category?: string | null;
  icon?: string | null;
  maxToolCalls?: number;
  requiresConfirmationForWrite?: boolean;
  metadata?: Record<string, unknown> | null;
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
  maxToolCalls?: number;
  requiresConfirmationForWrite?: boolean;
};

export type ShareChatAgentPayload = {
  targetUserId: string;
  role: "viewer" | "editor" | string;
};

export type ChatAgentExportBundle = {
  exportVersion: number;
  exportedAt: string;
  suggestedKey?: string;
  agent: {
    name: string;
    description?: string | null;
    systemPrompt?: string | null;
    category?: string | null;
    icon?: string | null;
    responseStyle?: string | null;
    visibility?: string;
    enabled?: boolean;
    maxToolCalls?: number;
    requiresConfirmationForWrite?: boolean;
    metadata?: Record<string, unknown> | null;
  };
  actionProviders: Array<{
    providerKey: string;
    enabled: boolean;
    allowRead: boolean;
    allowWrite: boolean;
    allowAdmin: boolean;
    requiresConfirmationForWrite: boolean;
  }>;
  actions: Array<{
    providerKey: string;
    actionId: string;
    enabled: boolean;
    sensitivity: string;
    requiresConfirmation: boolean;
  }>;
};

export type ChatAgentStats = {
  agentKey: string;
  windowHours: number;
  sessionsInWindow: number;
  messagesInWindow: number;
  totalSessions: number;
  actionProvidersCount: number;
  sharesCount: number;
};

export type ChatDirectoryUser = {
  id: string;
  name: string;
  email: string;
};

export type ChatAgentShare = {
  id: string;
  target_user_id: string;
  target_user_name?: string | null;
  target_user_email?: string | null;
  role: "viewer" | "editor" | string;
  created_at: string | null;
};

export type ChatProjectShare = ChatAgentShare;

export type ChatAgentPreviewResponse = {
  answer?: string | null;
  answerPreview?: string | null;
  rag?: Record<string, unknown>;
  toolCalls?: ChatToolCall[];
  plannedToolCalls?: ChatToolCall[];
  [key: string]: unknown;
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


export type ChatWorkspaceSource = {
  id: string;
  title: string;
  source_type: string;
  source_ref: string | null;
  scope: string | null;
  project_id: string | null;
  agent_key: string | null;
  attachment_id: string | null;
  original_filename: string | null;
  content_type: string | null;
  active: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  chunk_count: number | null;
  duplicate?: boolean;
};

export type ChatActionCatalogItem = {
  id: string;
  actionId: string;
  operationId?: string | null;
  method?: string | null;
  path?: string | null;
  summary?: string | null;
  description?: string | null;
  tags?: string[];
  parametersSchema?: Array<Record<string, unknown>>;
  requestBodySchema?: Record<string, unknown> | null;
  responseSchema?: Record<string, unknown> | null;
  sensitivity?: "read" | "write" | "admin" | string;
  enabled?: boolean;
  deprecated?: boolean;
};

export type ChatAgentAction = {
  id: string;
  agentId: string;
  providerKey: string;
  actionId: string;
  enabled: boolean;
  sensitivity: "read" | "write" | "admin" | string;
  requiresConfirmation: boolean;
  createdAt: string;
  updatedAt: string;
};

export type ChatSkillCatalogItem = {
  skillKey: string;
  label: string;
  description: string;
  policyFile: string;
  metadataFlag: string;
  executionHint?: string | null;
};

export type ChatAgentSkillBinding = {
  skillKey: string;
  label: string;
  description: string;
  policyFile: string;
  enabled: boolean;
  executionHint?: string | null;
  derived?: {
    sqlExecutionAvailable?: boolean;
  };
};

export type UpsertChatAgentSkillPayload = {
  skillKey: string;
  enabled: boolean;
};

export type ChatActionProvider = {
  id: string;
  providerKey: string;
  name: string;
  type: string;
  baseUrl: string;
  openApiUrl: string | null;
  privacyPolicyUrl?: string | null;
  authMode: string;
  authConfig?: Record<string, unknown> | null;
  latestSchema?: Record<string, unknown> | null;
  latestSchemaHash?: string | null;
  latestSchemaImportedAt?: string | null;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
};

export type ChatAgentActionProvider = {
  id: string;
  agentId: string;
  providerKey: string;
  providerName: string;
  providerType: string | null;
  baseUrl: string | null;
  openApiUrl: string | null;
  privacyPolicyUrl?: string | null;
  enabled: boolean;
  allowRead: boolean;
  allowWrite: boolean;
  allowAdmin: boolean;
  requiresConfirmationForWrite: boolean;
  actionCount: number;
  createdAt: string;
  updatedAt: string;
};

export type ChatActionTestResult = {
  ok: boolean;
  statusCode: number | null;
  durationMs: number;
  url: string;
  responsePreview: string | null;
  errorMessage: string | null;
};

export type ChatActionTestLog = ChatActionTestResult & {
  id: string;
  providerKey: string;
  actionId: string;
  method: string;
  requestPayload: Record<string, unknown> | null;
  createdAt: string | null;
};


export type ChatCapabilities = {
  permissions: string[];
  isSuperadmin: boolean;
  canOpenAdmin: boolean;
  canManageAgents: boolean;
  canManageOwnAgents: boolean;
  canManageOfficialAgents: boolean;
  canManageTools: boolean;
  canUseTools: boolean;
};
