import type {
  ChatMessage,
  ChatSession,
  CreateChatSessionPayload,
  SendChatMessagePayload,
  SendChatMessageResponse,
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
  options: ChatApiOptions = {},
): Promise<ChatSession[]> {
  const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
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
