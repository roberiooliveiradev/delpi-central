import type {
  ChatMessage,
  ChatSession,
  CreateChatSessionPayload,
} from "./chatTypes";

const API_BASE_URL = "/apps/minha-delpi-ai/api";

type TokenProvider = () => string | undefined | Promise<string | undefined>;

type ChatApiOptions = {
  getAccessToken?: TokenProvider;
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

import type {
  SendChatMessagePayload,
  SendChatMessageResponse,
} from "./chatTypes";

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
