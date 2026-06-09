import type {
  ChatActionCatalogItem,
  ChatActionProvider,
  ChatActionTestLog,
  ChatCapabilities,
  ChatActionTestResult,
  ChatAgent,
  ChatAgentActionProvider,
  ChatAgentExportBundle,
  ChatAgentAction,
  ChatAgentSkillBinding,
  ChatSkillCatalogItem,
  UpsertChatAgentSkillPayload,
  ChatAgentPreviewResponse,
  ChatAgentPreviewDraft,
  ChatAgentShare,
  ChatAgentVersion,
  ChatAgentStats,
  ChatProjectShare,
  ChatDirectoryUser,
  AssistantCatalogResponse,
  ChatArtifact,
  ChatAttachment,
  ChatMessage,
  ChatMessageFeedbackResponse,
  ChatFeedbackReasonsPayload,
  ChatProject,
  ChatSession,
  ChatStreamActivityEntry,
  ChatWorkspaceSource,
  CreateChatAgentPayload,
  CreateChatArtifactPayload,
  CreateChatProjectPayload,
  CreateChatSessionPayload,
  ChatCanvasOpenPayload,
  ChatPlaybackEvent,
  ChatResponseModeId,
  ChatResponseModesResponse,
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
  onStatus?: (message: string) => void;
  onActivity?: (entry: ChatStreamActivityEntry) => void;
  onSources?: (sources: SendChatMessageResponse["sources"]) => void;
  onToolCalls?: (toolCalls: SendChatMessageResponse["toolCalls"]) => void;
  onToken?: (token: string) => void;
  onUserPersisted?: (messageId: string) => void;
  onSessionRenamed?: (title: string) => void;
  onAssistantPending?: (messageId: string) => void;
  onPlayback?: (payload: ChatPlaybackEvent) => void;
  onCanvasOpen?: (payload: ChatCanvasOpenPayload) => void;
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

function extractApiErrorMessage(
  payload: unknown,
  response: Response,
  fallback: string,
): string {
  if (payload && typeof payload === "object") {
    const errors = (payload as { errors?: Array<{ message?: string }> }).errors;

    if (errors?.[0]?.message) {
      return errors[0].message;
    }

    const message = (payload as { message?: string }).message;

    if (message) {
      return message;
    }
  }

  return `${fallback} (HTTP ${response.status})`;
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const raw = await response.text();
  let payload: unknown = null;

  if (raw) {
    try {
      payload = JSON.parse(raw) as unknown;
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    if (!payload && raw.trim()) {
      throw new Error(
        `Erro ao comunicar com o Minha DELPI Chat. (HTTP ${response.status}: ${raw.trim().slice(0, 180)})`,
      );
    }

    throw new Error(
      extractApiErrorMessage(
        payload,
        response,
        "Erro ao comunicar com o Minha DELPI Chat.",
      ),
    );
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

export async function getAssistantCatalog(
  options: ChatApiOptions & {
    query?: string;
    agentId?: string;
    profileId?: string;
    limit?: number;
  } = {},
): Promise<AssistantCatalogResponse> {
  const params = new URLSearchParams();

  if (options.query?.trim()) {
    params.set("q", options.query.trim());
  }

  if (options.agentId?.trim()) {
    params.set("agentId", options.agentId.trim());
  }

  if (options.profileId?.trim()) {
    params.set("profileId", options.profileId.trim());
  }

  if (typeof options.limit === "number") {
    params.set("limit", String(options.limit));
  }

  const queryString = params.toString();
  const url = queryString
    ? `${API_BASE_URL}/chat/assistant/catalog?${queryString}`
    : `${API_BASE_URL}/chat/assistant/catalog`;

  const response = await fetch(url, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<AssistantCatalogResponse>(response);
}

export async function recordAssistantHelpEvent(
  payload: { event: string; metadata?: Record<string, unknown> | null },
  options: ChatApiOptions = {},
): Promise<{ ok: boolean; event: string }> {
  const response = await fetch(`${API_BASE_URL}/chat/assistant/help-events`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<{ ok: boolean; event: string }>(response);
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

export async function getChatResponseModes(
  options: ChatApiOptions = {},
): Promise<ChatResponseModesResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/response-modes`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatResponseModesResponse>(response);
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

export async function cancelChatStream(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<{ cancelled: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/messages/cancel`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<{ cancelled: boolean }>(response);
}

export async function switchChatBranch(
  sessionId: string,
  anchorUserMessageId: string,
  options: ChatApiOptions = {},
): Promise<ChatMessage[]> {
  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/active-branch`,
    {
      method: "PATCH",
      headers: await getAuthHeaders(options),
      body: JSON.stringify({ anchorUserMessageId }),
    },
  );

  return parseJsonResponse<ChatMessage[]>(response);
}

export async function upsertChatMessageFeedback(
  sessionId: string,
  messageId: string,
  rating: -1 | 1 | null,
  options: ChatApiOptions = {},
  reason?: string | null,
  comment?: string | null,
): Promise<ChatMessageFeedbackResponse> {
  const body: {
    rating: -1 | 1 | null;
    reason?: string;
    comment?: string;
  } = { rating };

  if (reason) {
    body.reason = reason;
  }

  if (comment) {
    body.comment = comment;
  }

  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/messages/${messageId}/feedback`,
    {
      method: "PUT",
      headers: await getAuthHeaders(options),
      body: JSON.stringify(body),
    },
  );

  return parseJsonResponse<ChatMessageFeedbackResponse>(response);
}

export async function getChatFeedbackReasons(
  options: ChatApiOptions = {},
): Promise<ChatFeedbackReasonsPayload> {
  const response = await fetch(`${API_BASE_URL}/chat/assistant/feedback-reasons`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatFeedbackReasonsPayload>(response);
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

function isAbortError(error: unknown, signal?: AbortSignal): boolean {
  if (signal?.aborted) {
    return true;
  }

  return error instanceof DOMException && error.name === "AbortError";
}

async function consumeChatMessageStream(
  response: Response,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  if (!response.body) {
    throw new Error("Erro ao iniciar streaming do Minha DELPI Chat.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let receivedDone = false;
  let streamErrorMessage: string | null = null;

  try {
  while (true) {
    if (signal?.aborted) {
      try {
        await reader.cancel();
      } catch {
        // ignore cancel errors
      }
      throw new DOMException("The operation was aborted.", "AbortError");
    }

    const { value, done } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      if (signal?.aborted) {
        throw new DOMException("The operation was aborted.", "AbortError");
      }
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

      if (event === "status") {
        callbacks.onStatus?.(
          typeof data.message === "string" ? data.message : "",
        );
      }

      if (event === "activity") {
        const entry = data.entry;

        if (entry && typeof entry === "object" && typeof (entry as { message?: unknown }).message === "string") {
          callbacks.onActivity?.(entry as ChatStreamActivityEntry);
        }
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

      if (event === "user_persisted") {
        const messageId =
          typeof data.messageId === "string" ? data.messageId : "";

        if (messageId) {
          callbacks.onUserPersisted?.(messageId);
        }
      }

      if (event === "session_renamed") {
        const title = typeof data.title === "string" ? data.title.trim() : "";

        if (title) {
          callbacks.onSessionRenamed?.(title);
        }
      }

      if (event === "assistant_pending") {
        const messageId =
          typeof data.messageId === "string" ? data.messageId : "";

        if (messageId) {
          callbacks.onAssistantPending?.(messageId);
        }
      }

      if (event === "playback") {
        callbacks.onPlayback?.({
          messageId: String(data.messageId ?? ""),
          answer: typeof data.answer === "string" ? data.answer : "",
          sources: (data.sources as SendChatMessageResponse["sources"]) ?? [],
          toolCalls: (data.toolCalls as SendChatMessageResponse["toolCalls"]) ?? [],
          adminDebug:
            (data.adminDebug as Record<string, unknown> | null | undefined) ?? null,
          metadata:
            (data.metadata as SendChatMessageResponse["metadata"]) ?? null,
        });
      }

      if (event === "canvas_open") {
        callbacks.onCanvasOpen?.({
          title: typeof data.title === "string" ? data.title : "",
          markdown: typeof data.markdown === "string" ? data.markdown : "",
          messageId: typeof data.messageId === "string" ? data.messageId : null,
          sourceMessageId:
            typeof data.sourceMessageId === "string" ? data.sourceMessageId : null,
        });
      }

      if (event === "done") {
        receivedDone = true;
        callbacks.onDone?.(data as SendChatMessageResponse);
      }

      if (event === "error") {
        streamErrorMessage =
          typeof data.detail === "string" && data.detail.trim()
            ? data.detail
            : typeof data.message === "string"
              ? data.message
              : "Erro durante streaming.";
        callbacks.onError?.(streamErrorMessage);
      }
    }
  }
  } catch (error) {
    if (isAbortError(error, signal)) {
      throw new DOMException("The operation was aborted.", "AbortError");
    }

    throw error;
  } finally {
    reader.releaseLock?.();
  }

  if (signal?.aborted) {
    throw new DOMException("The operation was aborted.", "AbortError");
  }

  if (streamErrorMessage) {
    throw new Error(streamErrorMessage);
  }

  if (!receivedDone) {
    throw new Error(
      "A conexão de streaming foi encerrada antes da resposta ser concluída.",
    );
  }
}

async function openChatMessageStream(
  url: string,
  body: Record<string, unknown>,
  callbacks: StreamCallbacks,
  options: ChatApiOptions & { signal?: AbortSignal } = {},
): Promise<void> {
  let response: Response;

  try {
    response = await fetch(url, {
      method: "POST",
      headers: await getAuthHeaders(options),
      body: JSON.stringify(body),
      signal: options.signal,
    });
  } catch (error) {
    if (isAbortError(error, options.signal)) {
      throw new DOMException("The operation was aborted.", "AbortError");
    }

    throw error;
  }

  if (!response.ok || !response.body) {
    const raw = await response.text();
    let errorPayload: unknown = null;

    if (raw) {
      try {
        errorPayload = JSON.parse(raw) as unknown;
      } catch {
        errorPayload = null;
      }
    }

    if (!errorPayload && raw.trim()) {
      throw new Error(
        `Erro ao iniciar streaming do Minha DELPI Chat. (HTTP ${response.status}: ${raw.trim().slice(0, 180)})`,
      );
    }

    throw new Error(
      extractApiErrorMessage(
        errorPayload,
        response,
        "Erro ao iniciar streaming do Minha DELPI Chat.",
      ),
    );
  }

  await consumeChatMessageStream(response, callbacks, options.signal);
}

export async function streamChatMessage(
  sessionId: string,
  payload: SendChatMessagePayload,
  callbacks: StreamCallbacks,
  options: ChatApiOptions & { signal?: AbortSignal } = {},
): Promise<void> {
  await openChatMessageStream(
    `${API_BASE_URL}/chat/sessions/${sessionId}/messages/stream`,
    payload,
    callbacks,
    options,
  );
}

export async function resendChatMessage(
  sessionId: string,
  messageId: string,
  content: string,
  callbacks: StreamCallbacks,
  options: ChatApiOptions & {
    signal?: AbortSignal;
    context?: string;
    responseMode?: ChatResponseModeId;
  } = {},
): Promise<void> {
  await openChatMessageStream(
    `${API_BASE_URL}/chat/sessions/${sessionId}/messages/${messageId}/resend/stream`,
    {
      content,
      context: options.context,
      responseMode: options.responseMode,
    },
    callbacks,
    options,
  );
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

export async function clearChatSessionMemory(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<{ cleared: number }> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/memory/clear`, {
    method: "POST",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<{ cleared: number }>(response);
}

export type SessionMemoryUsageView = {
  layers?: string[];
  topic?: string | null;
  task?: string | null;
  operationalFocus?: Record<string, string>;
  preferences?: string[];
  resolvedReferences?: string[];
  semanticHits?: Array<{ title?: string; snippet?: string }>;
  episodicCount?: number;
  episodicRecall?: string | null;
  writeGated?: boolean;
};

export type SessionMemoryContextResponse = {
  chips: Array<{ label: string; kind: string; value: string }>;
  summary?: string | null;
  usage?: SessionMemoryUsageView | null;
};

export async function getChatSessionMemoryContext(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<SessionMemoryContextResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/memory/context`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<SessionMemoryContextResponse>(response);
}

export type ChatSessionContextItemPayload = {
  content: string;
  filename?: string;
  role?: "user" | "assistant";
  kind?: "question" | "answer";
  messageId?: string;
  question?: string;
  answer?: string;
  questionMessageId?: string;
  answerMessageId?: string;
};

export async function addChatSessionContextItem(
  sessionId: string,
  payload: ChatSessionContextItemPayload,
  options: ChatApiOptions = {},
): Promise<SessionMemoryContextResponse> {
  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/memory/context-items`,
    {
      method: "POST",
      headers: await getAuthHeaders(options),
      body: JSON.stringify(payload),
    },
  );

  return parseJsonResponse<SessionMemoryContextResponse>(response);
}

export async function removeChatSessionContextItem(
  sessionId: string,
  itemId: string,
  options: ChatApiOptions = {},
): Promise<SessionMemoryContextResponse> {
  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/memory/context-items/${encodeURIComponent(itemId)}`,
    {
      method: "DELETE",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<SessionMemoryContextResponse>(response);
}

export async function addChatSessionMemoryPin(
  sessionId: string,
  payload: { kind: string; value: string },
  options: ChatApiOptions = {},
): Promise<SessionMemoryContextResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/memory/pins`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<SessionMemoryContextResponse>(response);
}

export async function removeChatSessionMemoryPin(
  sessionId: string,
  kind: string,
  options: ChatApiOptions = {},
): Promise<SessionMemoryContextResponse> {
  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/memory/pins/${encodeURIComponent(kind)}`,
    {
      method: "DELETE",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<SessionMemoryContextResponse>(response);
}

export async function setChatSessionResponseFormat(
  sessionId: string,
  responseFormat: string,
  options: ChatApiOptions = {},
): Promise<SessionMemoryContextResponse> {
  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/memory/response-format`,
    {
      method: "PUT",
      headers: await getAuthHeaders(options),
      body: JSON.stringify({ responseFormat }),
    },
  );

  return parseJsonResponse<SessionMemoryContextResponse>(response);
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

export async function exportChatAgent(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatAgentExportBundle> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/export`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgentExportBundle>(response);
}

export async function importChatAgent(
  payload: {
    export: ChatAgentExportBundle;
    key?: string;
    name?: string;
    visibility?: string;
    applyActions?: boolean;
  },
  options: ChatApiOptions = {},
): Promise<ChatAgent> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/import`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
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
  options: ChatApiOptions & {
    hours?: number;
    specialization?: { enabled: boolean; allowedTools?: string[] };
  } = {},
): Promise<ChatAgentStats> {
  const params = new URLSearchParams({
    hours: String(options.hours ?? 168),
  });

  if (options.specialization) {
    params.set("specialization", JSON.stringify(options.specialization));
  }
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/stats?${params}`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgentStats>(response);
}

export async function previewChatAgent(
  agentId: string,
  payload: {
    message: string;
    generateAnswer?: boolean;
    draft?: ChatAgentPreviewDraft;
  },
  options: ChatApiOptions = {},
): Promise<ChatAgentPreviewResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/preview`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse(response);
}

export async function previewChatAgentDraft(
  payload: {
    message: string;
    generateAnswer?: boolean;
    draft: ChatAgentPreviewDraft;
  },
  options: ChatApiOptions = {},
): Promise<ChatAgentPreviewResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/preview`, {
    method: "POST",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse(response);
}

export async function publishChatAgent(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatAgent> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/publish`, {
    method: "POST",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgent>(response);
}

export async function listChatAgentVersions(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatAgentVersion[]> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/versions`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgentVersion[]>(response);
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


export async function fetchChatSessionAttachments(
  sessionId: string,
  options: ChatApiOptions = {},
): Promise<ChatAttachment[]> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/attachments`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAttachment[]>(response);
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
    agentId?: string | null;
    context?: string | null;
  } = {},
  options: ChatApiOptions = {},
): Promise<{ session: ChatSession; attachment: ChatAttachment }> {
  const formData = new FormData();
  formData.append("file", file);

  if (payload.projectId) {
    formData.append("projectId", payload.projectId);
  }

  if (payload.agentId) {
    formData.append("agentId", payload.agentId);
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

async function downloadBinaryFromChat(
  path: string,
  options: ChatApiOptions = {},
): Promise<void> {
  const { parseContentDispositionFilename, triggerBlobDownload } = await import(
    "../../utils/downloadBlob"
  );

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: await getAuthOnlyHeaders(options),
  });

  if (!response.ok) {
    await parseJsonResponse<unknown>(response);
  }

  const blob = await response.blob();
  const filename =
    parseContentDispositionFilename(response.headers.get("Content-Disposition")) ||
    "download";

  triggerBlobDownload(blob, filename);
}

export async function downloadChatAttachment(
  attachmentId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  await downloadBinaryFromChat(`/chat/attachments/${attachmentId}/download`, options);
}

export async function downloadChatSource(
  sourceId: string,
  options: ChatApiOptions = {},
): Promise<void> {
  await downloadBinaryFromChat(`/chat/sources/${sourceId}/download`, options);
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

export async function listChatSkillCatalog(
  options: ChatApiOptions = {},
): Promise<ChatSkillCatalogItem[]> {
  const response = await fetch(`${API_BASE_URL}/chat/skills`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatSkillCatalogItem[]>(response);
}

export async function listChatAgentSkills(
  agentId: string,
  options: ChatApiOptions = {},
): Promise<ChatAgentSkillBinding[]> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/skills`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgentSkillBinding[]>(response);
}

export async function upsertChatAgentSkill(
  agentId: string,
  payload: UpsertChatAgentSkillPayload,
  options: ChatApiOptions = {},
): Promise<{ ok: boolean }> {
  const response = await fetch(`${API_BASE_URL}/chat/agents/${agentId}/skills`, {
    method: "PUT",
    headers: await getAuthHeaders(options),
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<{ ok: boolean }>(response);
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

export async function deleteChatAgentActionProvider(
  agentId: string,
  providerKey: string,
  options: ChatApiOptions = {},
): Promise<{ deleted: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/chat/agents/${agentId}/providers/${encodeURIComponent(providerKey)}`,
    {
      method: "DELETE",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<{ deleted: boolean }>(response);
}

export async function deleteChatAgentAction(
  agentId: string,
  providerKey: string,
  actionId: string,
  options: ChatApiOptions = {},
): Promise<{ deleted: boolean }> {
  const encodedProvider = encodeURIComponent(providerKey);
  const encodedAction = encodeURIComponent(actionId);
  const response = await fetch(
    `${API_BASE_URL}/chat/agents/${agentId}/providers/${encodedProvider}/actions/${encodedAction}`,
    {
      method: "DELETE",
      headers: await getAuthHeaders(options),
    },
  );

  return parseJsonResponse<{ deleted: boolean }>(response);
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
