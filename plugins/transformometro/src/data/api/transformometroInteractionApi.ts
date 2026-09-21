import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";
import { parseApiEnvelope } from "./transformometroHttp";

export const INTERACTION_MESSAGE_MAX_LENGTH = 4000;

export type InteractionRoomDto = {
  id: string;
  processo_id: string;
  processo_codigo: string;
  processo_nome: string;
  created_by_user_id: string;
  created_at?: string | null;
  updated_at?: string | null;
  last_message_preview?: string | null;
  last_message_at?: string | null;
};

export type InteractionMessageDto = {
  id: string;
  room_id: string;
  author_user_id: string;
  content: string;
  created_at?: string | null;
};

export type InteractionMessagePage = {
  items: InteractionMessageDto[];
  has_more: boolean;
};

async function request<T>(
  path: string,
  getAccessToken?: () => string | undefined,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}${path}`, {
    ...init,
    headers: {
      ...buildAuthHeaders(getAccessToken),
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  return parseApiEnvelope<T>(response);
}

export function listInteractionRooms(getAccessToken?: () => string | undefined) {
  return request<{ items: InteractionRoomDto[] }>("/interaction-rooms", getAccessToken);
}

export function openInteractionRoom(
  processoId: string,
  getAccessToken?: () => string | undefined,
) {
  return request<InteractionRoomDto>("/interaction-rooms", getAccessToken, {
    method: "POST",
    body: JSON.stringify({ processo_id: processoId }),
  });
}

export function getInteractionRoom(roomId: string, getAccessToken?: () => string | undefined) {
  return request<InteractionRoomDto>(`/interaction-rooms/${roomId}`, getAccessToken);
}

export function listInteractionMessages(
  roomId: string,
  getAccessToken?: () => string | undefined,
  limit = 50,
) {
  return request<InteractionMessagePage>(
    `/interaction-rooms/${roomId}/messages?limit=${encodeURIComponent(String(limit))}`,
    getAccessToken,
  );
}

export function postInteractionMessage(
  roomId: string,
  content: string,
  getAccessToken?: () => string | undefined,
) {
  return request<InteractionMessageDto>(`/interaction-rooms/${roomId}/messages`, getAccessToken, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}
