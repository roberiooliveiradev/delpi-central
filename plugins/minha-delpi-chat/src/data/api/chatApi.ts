import type {
  ChatActionCatalogItem,
  ChatActionProvider,
  ChatActionTestLog,
  ChatCapabilities,
  ChatActionTestResult,
  ChatAgent,
  ChatAgentActionProvider,
  ChatAgentAction,
  ChatAgentPreviewResponse,
  ChatAgentShare,
  ChatAgentStats,
  ChatProjectShare,
  ChatDirectoryUser,
  ChatArtifact,
  ChatAttachment,
  ChatMessage,
  ChatMessageFeedbackResponse,
  ChatProject,
  ChatSession,
  ChatWorkspaceSource,
  CreateChatAgentPayload,
  CreateChatArtifactPayload,
  CreateChatProjectPayload,
  CreateChatSessionPayload,
  SendChatMessagePayload,
  SendChatMessageResponse,
  ShareChatAgentPayload,
  ShareChatProjectPayload,
  UpdateChatAgentPayload,
  UpdateChatArtifactPayload,
  UpdateChatProjectPayload,
  UpsertChatAgentActionPayload,
} from "./chatTypes";

const API_BASE_URL = "/apps/minha-delpi-ai/api";

type TokenProvider = () => string | undefined | Promise<string | undefined>;

type ChatApiOptions = {
  getAccessToken?: TokenProvider;
};

type StreamCallbacks = {
  onSources?: (sources: SendChatMessageResponse["sources"]) => void;
  onToolCalls?: (toolCalls: SendChatMessageResponse["toolCalls"]) => void;
  onToken?: (token: string) => void;
  onDone?: (response: SendChatMessageResponse) => void;
  onError?: (message: string) => void;
};

async function getAuthOnlyHeaders(options: ChatApiOptions): Promise<HeadersInit> {
  const token = await options.getAccessToken?.();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

async function getAuthHeaders(options: ChatApiOptions): Promise<HeadersInit> {
  const token = await options.getAccessToken?.();

  if (!token) {
    return {
      "Content-Type": "application/json",
    };
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      payload?.errors?.[0]?.message ??
      payload?.message ??
      "Erro ao comunicar com o Minha DELPI Chat.";

    throw new Error(message);
  }

  return payload as T;
}

export async function getChatCapabilities(
  options: ChatApiOptions = {},
): Promise<ChatCapabilities> {
  const response = await fetch(`${API_BASE_URL}/chat/capabilities`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatCapabilities>(response);
}


export async function createChatSession(
  payload: CreateChatSessionPayload,
  options: ChatApiOptions = {},
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatSession>(response);
}

export async function listChatSessions(
  options: ChatApiOptions & { archived?: boolean } = {},
): Promise<ChatSession[]> {
  const params = new URLSearchParams();

  if (options.archived) {
    params.set("archived", "true");
  }

  const queryString = params.toString();
  const url = queryString
    ? `${API_BASE_URL}/chat/sessions?${queryString}`
    : `${API_BASE_URL}/chat/sessions`;

  const response = await fetch(url, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatSession[]>(response);
}

export async function listChatMessages(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<ChatMessage[]> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatMessage[]>(response);
}

export async function upsertChatMessageFeedback(
  sessionId: string,
  messageId: string,
  rating: -1 | 1 | null,
  options: ChatApiOptions = {},
): Promise<ChatMessageFeedbackResponse> {
  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/messages/${messageId}/feedback`,
    {
      method: "PUT",
      headers: await getAuthHeaders(options),
      body: JSON.stringify({ rating }),
    },
  );

  return parseJsonResponse<ChatMessageFeedbackResponse>(response);
}

export async function sendChatMessage(
  sessionId: string,
  payload: SendChatMessagePayload,
  options: ChatApiOptions = {},
): Promise<SendChatMessageResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<SendChatMessageResponse>(response);
}

export async function streamChatMessage(
  sessionId: string,
  payload: SendChatMessagePayload,
  callbacks: StreamCallbacks,
  options: ChatApiOptions & { signal?: AbortSignal } = {},
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/messages/stream`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
      body: JSON.stringify(payload),
      signal: options.signal,
    },
  );

  if (!response.ok || !response.body) {
    const errorPayload = await response.json().catch(() => null);
    const message =
      errorPayload?.errors?.[0]?.message ??
      "Erro ao iniciar streaming do Minha DELPI Chat.";

    throw new Error(message);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const lines = part.split("\n");
      const event = lines
        .find((line) => line.startsWith("event:"))
        ?.replace("event:", "")
        .trim();

      const dataLine = lines.find((line) => line.startsWith("data:"));
      const rawData = dataLine?.replace("data:", "").trim();

      if (!event || !rawData) {
        continue;
      }

      let data: Record<string, unknown>;

      try {
        data = JSON.parse(rawData) as Record<string, unknown>;
      } catch {
        callbacks.onError?.("Recebi uma resposta de streaming em formato inválido.");
        continue;
      }

      if (event === "sources") {
        callbacks.onSources?.((data.sources as SendChatMessageResponse["sources"]) ?? []);
      }

      if (event === "tool_calls") {
        callbacks.onToolCalls?.((data.toolCalls as SendChatMessageResponse["toolCalls"]) ?? []);
      }

      if (event === "token") {
        callbacks.onToken?.(typeof data.content === "string" ? data.content : "");
      }

      if (event === "done") {
        callbacks.onDone?.(data as SendChatMessageResponse);
      }

      if (event === "error") {
        callbacks.onError?.(
          typeof data.detail === "string" && data.detail.trim()
            ? data.detail
            : typeof data.message === "string"
              ? data.message
              : "Erro durante streaming.",
        );
      }
    }
  }
}

export async function renameChatSession(
  sessionId: string,
  title: string,
  options: ChatApiOptions = {},
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
    body: JSON.stringify({ title }),
  });

  return parseJsonResponse<ChatSession>(response);
}

export async function deleteChatSession(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: await getAuthHeaders(options),
  });

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }
}

export async function updateChatMessage(
  messageId: string,
  content: string,
  options: ChatApiOptions = {},
): Promise<ChatMessage> {
  const response = await fetch(`${API_BASE_URL}/chat/messages/${messageId}`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
    body: JSON.stringify({ content }),
  });

  return parseJsonResponse<ChatMessage>(response);
}


export async function pinChatSession(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/pin`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatSession>(response);
}

export async function unpinChatSession(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/unpin`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatSession>(response);
}

export async function archiveChatSession(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/archive`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatSession>(response);
}

export async function unarchiveChatSession(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/unarchive`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatSession>(response);
}


export async function listChatArtifacts(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<ChatArtifact[]> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/artifacts`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatArtifact[]>(response);
}

export async function createChatArtifact(
  sessionId: string,
  payload: CreateChatArtifactPayload,
  options: ChatApiOptions = {},
): Promise<ChatArtifact> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/artifacts`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatArtifact>(response);
}

export async function updateChatArtifact(
  artifactId: string,
  payload: UpdateChatArtifactPayload,
  options: ChatApiOptions = {},
): Promise<ChatArtifact> {
  const response = await fetch(`${API_BASE_URL}/chat/artifacts/${artifactId}`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatArtifact>(response);
}

export async function deleteChatArtifact(
  artifactId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/artifacts/${artifactId}`, {
    method: "DELETE",
    headers: await getAuthHeaders(options),
  });

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }
}


export async function listChatAgents(
  options: ChatApiOptions & {
    includeDisabled?: boolean;
    includeStats?: boolean;
    statsHours?: number;
  } = {},
): Promise<ChatAgent[]> {
  const params = new URLSearchParams();

  if (options.includeDisabled) {
    params.set("includeDisabled", "true");
  }

  if (options.includeStats) {
    params.set("includeStats", "true");
    params.set("hours", String(options.statsHours ?? 168));
  }

  const query = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/chat/agents${query}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgent[]>(response);
}

export async function getChatAgent(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatAgent> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgent>(response);
}

export async function createChatAgent(
  payload: CreateChatAgentPayload,
  options: ChatApiOptions = {},
): Promise<ChatAgent> {
  const response = await fetch(`${API_BASE_URL}/chat/agents`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatAgent>(response);
}

export async function updateChatAgent(
  agentId: string,
  payload: UpdateChatAgentPayload,
  options: ChatApiOptions = {},
): Promise<ChatAgent> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatAgent>(response);
}

export async function deleteChatAgent(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}`, {
    method: "DELETE",
    headers: await getAuthHeaders(options),
  });

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }
}

export async function shareChatAgent(
  agentId: string,
  payload: ShareChatAgentPayload,
  options: ChatApiOptions = {},
): Promise<{ ok: boolean }> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/share`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<{ ok: boolean }>(response);
}

export async function listChatAgentShares(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatAgentShare[]> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/shares`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse(response);
}

export async function revokeChatAgentShare(
  agentId: string,
  targetUserId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/chat/agents/${agentId}/shares/${targetUserId}`,
    {
      method: "DELETE",
      headers: await getAuthHeaders(options),
    },
  );

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }
}

export async function searchChatUsers(
  query: string,
  options: ChatApiOptions & { limit?: number } = {},
): Promise<ChatDirectoryUser[]> {
  const params = new URLSearchParams({
    q: query,
    limit: String(options.limit ?? 10),
  });
  const response = await fetch(`${API_BASE_URL}/chat/users/search?${params}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });
  const payload = await parseJsonResponse<{ items: ChatDirectoryUser[] }>(response);

  return payload.items ?? [];
}

export async function duplicateChatAgent(
  agentId: string,
  options: ChatApiOptions & { copyActions?: boolean; copySources?: boolean } = {},
): Promise<ChatAgent> {
  const { copyActions = true, copySources = false, ...apiOptions } = options;
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/duplicate`, {
    method: "POST",
    headers: await getAuthHeaders(apiOptions),
    body: JSON.stringify({ copyActions, copySources }),
  });

  return parseJsonResponse<ChatAgent>(response);
}

export async function transferChatAgentOwnership(
  agentId: string,
  newOwnerUserId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/transfer`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify({ newOwnerUserId }),
  });

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }
}

export async function getChatAgentStats(
  agentId: string,
  options: ChatApiOptions & { hours?: number } = {},
): Promise<ChatAgentStats> {
  const params = new URLSearchParams({
    hours: String(options.hours ?? 168),
  });
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/stats?${params}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgentStats>(response);
}

export async function previewChatAgent(
  agentId: string,
  payload: { message: string; generateAnswer?: boolean },
  options: ChatApiOptions = {},
): Promise<ChatAgentPreviewResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/preview`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse(response);
}

export async function upsertChatAgentAction(
  agentId: string,
  payload: UpsertChatAgentActionPayload,
  options: ChatApiOptions = {},
): Promise<{ ok: boolean }> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/actions`, {
    method: "PUT",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<{ ok: boolean }>(response);
}

export async function listChatProjects(
  options: ChatApiOptions = {},
): Promise<ChatProject[]> {
  const response = await fetch(`${API_BASE_URL}/chat/projects`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatProject[]>(response);
}

export async function createChatProject(
  payload: CreateChatProjectPayload,
  options: ChatApiOptions = {},
): Promise<ChatProject> {
  const response = await fetch(`${API_BASE_URL}/chat/projects`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatProject>(response);
}

export async function updateChatProject(
  projectId: string,
  payload: UpdateChatProjectPayload,
  options: ChatApiOptions = {},
): Promise<ChatProject> {
  const response = await fetch(`${API_BASE_URL}/chat/projects/${projectId}`, {
    method: "PATCH",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatProject>(response);
}

export async function deleteChatProject(
  projectId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/projects/${projectId}`, {
    method: "DELETE",
    headers: await getAuthHeaders(options),
  });

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }
}


export async function listChatProjectShares(
  projectId: string,
  options: ChatApiOptions = {},
): Promise<ChatProjectShare[]> {
  const response = await fetch(`${API_BASE_URL}/chat/projects/${projectId}/shares`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse(response);
}

export async function revokeChatProjectShare(
  projectId: string,
  targetUserId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/chat/projects/${projectId}/shares/${targetUserId}`,
    {
      method: "DELETE",
      headers: await getAuthHeaders(options),
    },
  );

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }
}

export async function shareChatProject(
  projectId: string,
  payload: ShareChatProjectPayload,
  options: ChatApiOptions = {},
): Promise<{ ok: boolean }> {
  const response = await fetch(`${API_BASE_URL}/chat/projects/${projectId}/share`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<{ ok: boolean }>(response);
}


export async function uploadChatAttachment(
  sessionId: string,
  file: File,
  options: ChatApiOptions = {},
): Promise<ChatAttachment> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/attachments`, {
    method: "POST",
    headers: await getAuthOnlyHeaders(options),
    body: formData,
  });

  return parseJsonResponse<ChatAttachment>(response);
}

export async function uploadChatAttachmentWithSession(
  file: File,
  payload: {
    projectId?: string | null;
    agentKey?: string | null;
    context?: string | null;
  } = {},
  options: ChatApiOptions = {},
): Promise<{ session: ChatSession; attachment: ChatAttachment }> {
  const formData = new FormData();
  formData.append("file", file);

  if (payload.projectId) {
    formData.append("projectId", payload.projectId);
  }

  if (payload.agentKey) {
    formData.append("agentKey", payload.agentKey);
  }

  if (payload.context) {
    formData.append("context", payload.context);
  }

  const response = await fetch(`${API_BASE_URL}/chat/attachments`, {
    method: "POST",
    headers: await getAuthOnlyHeaders(options),
    body: formData,
  });

  return parseJsonResponse<{ session: ChatSession; attachment: ChatAttachment }>(response);
}

export async function listProjectSources(
  projectId: string,
  options: ChatApiOptions = {},
): Promise<ChatWorkspaceSource[]> {
  const response = await fetch(`${API_BASE_URL}/chat/projects/${projectId}/sources`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatWorkspaceSource[]>(response);
}

export async function uploadProjectSource(
  projectId: string,
  file: File,
  options: ChatApiOptions = {},
): Promise<ChatWorkspaceSource> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/chat/projects/${projectId}/sources`, {
    method: "POST",
    headers: await getAuthOnlyHeaders(options),
    body: formData,
  });

  return parseJsonResponse<ChatWorkspaceSource>(response);
}

export async function createProjectTextSource(
  projectId: string,
  payload: {
    title: string;
    content: string;
    metadata?: Record<string, unknown> | null;
  },
  options: ChatApiOptions = {},
): Promise<ChatWorkspaceSource> {
  const response = await fetch(`${API_BASE_URL}/chat/projects/${projectId}/sources`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatWorkspaceSource>(response);
}

export async function listAgentSources(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatWorkspaceSource[]> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/sources`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatWorkspaceSource[]>(response);
}

export async function uploadAgentSource(
  agentId: string,
  file: File,
  options: ChatApiOptions = {},
): Promise<ChatWorkspaceSource> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/sources`, {
    method: "POST",
    headers: await getAuthOnlyHeaders(options),
    body: formData,
  });

  return parseJsonResponse<ChatWorkspaceSource>(response);
}

export async function createAgentTextSource(
  agentId: string,
  payload: {
    title: string;
    content: string;
    metadata?: Record<string, unknown> | null;
  },
  options: ChatApiOptions = {},
): Promise<ChatWorkspaceSource> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/sources`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatWorkspaceSource>(response);
}

export async function deleteChatSource(
  sourceId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/sources/${sourceId}`, {
    method: "DELETE",
    headers: await getAuthHeaders(options),
  });

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }
}

export async function listChatActions(
  options: ChatApiOptions & { providerKey?: string | null } = {},
): Promise<ChatActionCatalogItem[]> {
  const params = new URLSearchParams();

  if (options.providerKey) {
    params.set("providerKey", options.providerKey);
  }

  const query = params.toString();
  const response = await fetch(
    query ? `${API_BASE_URL}/chat/actions?${query}` : `${API_BASE_URL}/chat/actions`,
    {
      method: "GET",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<ChatActionCatalogItem[]>(response);
}

export async function listChatAgentActions(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatAgentAction[]> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/actions`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgentAction[]>(response);
}


export async function listActionProviders(
  options: ChatApiOptions = {},
): Promise<ChatActionProvider[]> {
  const response = await fetch(`${API_BASE_URL}/chat/action-providers`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatActionProvider[]>(response);
}

export async function listChatAgentActionProviders(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatAgentActionProvider[]> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/providers`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgentActionProvider[]>(response);
}

export async function saveChatAgentActionProvider(
  agentId: string,
  payload: {
    providerKey: string;
    enabled?: boolean;
    allowRead?: boolean;
    allowWrite?: boolean;
    allowAdmin?: boolean;
    requiresConfirmationForWrite?: boolean;
  },
  options: ChatApiOptions = {},
): Promise<{ saved: boolean }> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/providers`, {
    method: "PUT",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<{ saved: boolean }>(response);
}


export async function createChatAgentActionProvider(
  agentId: string,
  payload: {
    providerKey: string;
    name: string;
    type?: string;
    baseUrl: string;
    openApiUrl?: string | null;
    privacyPolicyUrl?: string | null;
    schema?: Record<string, unknown> | null;
    authMode?: string;
    authConfig?: Record<string, unknown> | null;
    enabled?: boolean;
    allowRead?: boolean;
    allowWrite?: boolean;
    allowAdmin?: boolean;
    requiresConfirmationForWrite?: boolean;
  },
  options: ChatApiOptions = {},
): Promise<{
  provider: ChatActionProvider;
  import?: {
    found?: boolean;
    actionsImported?: number;
    schemaHash?: string;
  } | null;
  linked: boolean;
}> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/providers/create`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse(response);
}


export async function importChatAgentActionProviderSchema(
  agentId: string,
  providerKey: string,
  options: ChatApiOptions = {},
): Promise<{
  found?: boolean;
  actionsImported?: number;
  schemaHash?: string;
}> {
  const response = await fetch(
    `${API_BASE_URL}/chat/agents/${agentId}/providers/${providerKey}/import`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse(response);
}


export async function getChatAgentActionProvider(
  agentId: string,
  providerKey: string,
  options: ChatApiOptions = {},
): Promise<ChatActionProvider> {
  const response = await fetch(
    `${API_BASE_URL}/chat/agents/${agentId}/providers/${providerKey}`,
    {
      method: "GET",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<ChatActionProvider>(response);
}

export async function updateChatAgentActionProvider(
  agentId: string,
  providerKey: string,
  payload: {
    name?: string;
    baseUrl?: string;
    openApiUrl?: string | null;
    privacyPolicyUrl?: string | null;
    authMode?: string;
    authConfig?: Record<string, unknown> | null;
    enabled?: boolean;
  },
  options: ChatApiOptions = {},
): Promise<ChatActionProvider> {
  const response = await fetch(
    `${API_BASE_URL}/chat/agents/${agentId}/providers/${providerKey}`,
    {
      method: "PATCH",
      headers: await getAuthHeaders(options),
      body: JSON.stringify(payload),
    },
  );

  return parseJsonResponse<ChatActionProvider>(response);
}


export async function testChatAgentAction(
  agentId: string,
  providerKey: string,
  actionId: string,
  payload: {
    pathParams?: Record<string, string>;
    query?: Record<string, string>;
    body?: unknown;
  },
  options: ChatApiOptions = {},
): Promise<ChatActionTestResult> {
  const response = await fetch(
    `${API_BASE_URL}/chat/agents/${encodeURIComponent(agentId)}/providers/${encodeURIComponent(providerKey)}/actions/${encodeURIComponent(actionId)}/test`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
      body: JSON.stringify(payload),
    },
  );

  const responsePayload = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      responsePayload?.errors?.[0]?.message ??
      responsePayload?.message ??
      "Não foi possível testar esta rota.";

    return {
      ok: false,
      statusCode: response.status,
      durationMs: 0,
      url: "",
      responsePreview:
        responsePayload && typeof responsePayload === "object"
          ? JSON.stringify(responsePayload, null, 2)
          : null,
      errorMessage: message,
    };
  }

  return responsePayload as ChatActionTestResult;
}

export async function listChatAgentActionTestLogs(
  agentId: string,
  providerKey: string,
  actionId: string,
  options: ChatApiOptions = {},
): Promise<ChatActionTestLog[]> {
  const response = await fetch(
    `${API_BASE_URL}/chat/agents/${encodeURIComponent(agentId)}/providers/${encodeURIComponent(providerKey)}/actions/${encodeURIComponent(actionId)}/logs`,
    {
      method: "GET",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<ChatActionTestLog[]>(response);
}
