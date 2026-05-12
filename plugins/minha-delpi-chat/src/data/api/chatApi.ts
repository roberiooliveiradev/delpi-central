import type {
  ChatAgent,
  ChatArtifact,
  ChatMessage,
  ChatProject,
  ChatSession,
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

      const data = JSON.parse(rawData);

      if (event === "sources") {
        callbacks.onSources?.(data.sources ?? []);
      }

      if (event === "tool_calls") {
        callbacks.onToolCalls?.(data.toolCalls ?? []);
      }

      if (event === "token") {
        callbacks.onToken?.(data.content ?? "");
      }

      if (event === "done") {
        callbacks.onDone?.(data as SendChatMessageResponse);
      }

      if (event === "error") {
        callbacks.onError?.(data.message ?? "Erro durante streaming.");
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
  options: ChatApiOptions = {},
): Promise<ChatAgent[]> {
  const response = await fetch(`${API_BASE_URL}/chat/agents`, {
    method: "GET",
    headers: await getAuthHeaders(options),
  });

  return parseJsonResponse<ChatAgent[]>(response);
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
