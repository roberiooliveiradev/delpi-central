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
  unread_count?: number;
  mentioned?: boolean;
};

export type InteractionMentionDto = {
  user_id: string;
  label: string;
};

export type InteractionReactionDto = {
  user_id: string;
  code: string;
};

export type InteractionAttachmentDto = {
  id: string;
  message_id: string;
  room_id: string;
  file_name: string;
  content_type: string;
  byte_size: number;
  uploaded_by_user_id: string;
  created_at?: string | null;
};

export type InteractionMessageDto = {
  id: string;
  room_id: string;
  author_user_id: string;
  content: string;
  created_at?: string | null;
  parent_id?: string | null;
  edited_at?: string | null;
  deleted_at?: string | null;
  mentions?: InteractionMentionDto[];
  reactions?: InteractionReactionDto[];
  attachments?: InteractionAttachmentDto[];
  pinned?: boolean;
};

export type InteractionMessagePage = {
  items: InteractionMessageDto[];
  has_more: boolean;
};

export type InteractionInboxFilter = "all" | "process" | "unread" | "mentioned";

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

export function listInteractionRooms(
  getAccessToken?: () => string | undefined,
  inboxFilter: InteractionInboxFilter = "all",
) {
  const query = new URLSearchParams({ inbox_filter: inboxFilter });
  return request<{ items: InteractionRoomDto[] }>(`/interaction-rooms?${query}`, getAccessToken);
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
  options?: { limit?: number; beforeId?: string | null },
) {
  const params = new URLSearchParams();
  const limit = options?.limit ?? 50;
  params.set("limit", String(limit));
  if (options?.beforeId) params.set("before_id", options.beforeId);
  return request<InteractionMessagePage>(
    `/interaction-rooms/${roomId}/messages?${params}`,
    getAccessToken,
  );
}

export type PersonProfilePhotoFlagDto = {
  user_id: string;
  has_photo: boolean;
};

/** Batch flags for third-party avatars (user-parity JWT; soft-fail at caller). */
export function lookupPersonProfilePhotoFlags(
  ids: readonly string[],
  getAccessToken?: () => string | undefined,
) {
  const unique = [...new Set(ids.map((id) => id.trim()).filter(Boolean))].slice(0, 50);
  if (unique.length === 0) {
    return Promise.resolve({ items: [] as PersonProfilePhotoFlagDto[] });
  }
  const params = new URLSearchParams({ ids: unique.join(",") });
  return request<{ items: PersonProfilePhotoFlagDto[] }>(
    `/person-profiles/photo-flags?${params}`,
    getAccessToken,
  );
}

/** Download person-profile photo bytes via TM facade (never Core S2S from the MFE). */
export async function downloadPersonProfilePhoto(
  userId: string,
  getAccessToken?: () => string | undefined,
): Promise<Blob | null> {
  const uid = userId.trim();
  if (!uid) return null;
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/person-profiles/${encodeURIComponent(uid)}/photo`,
    { headers: buildAuthHeaders(getAccessToken) },
  );
  if (!response.ok) return null;
  return response.blob();
}

export function postInteractionMessage(
  roomId: string,
  content: string,
  getAccessToken?: () => string | undefined,
  extras?: { parentId?: string | null; mentions?: InteractionMentionDto[] },
) {
  return request<InteractionMessageDto>(`/interaction-rooms/${roomId}/messages`, getAccessToken, {
    method: "POST",
    body: JSON.stringify({
      content,
      parent_id: extras?.parentId ?? null,
      mentions: extras?.mentions ?? [],
    }),
  });
}

export function editInteractionMessage(
  roomId: string,
  messageId: string,
  content: string,
  getAccessToken?: () => string | undefined,
) {
  return request<InteractionMessageDto>(
    `/interaction-rooms/${roomId}/messages/${messageId}`,
    getAccessToken,
    { method: "PATCH", body: JSON.stringify({ content }) },
  );
}

export function deleteInteractionMessage(
  roomId: string,
  messageId: string,
  getAccessToken?: () => string | undefined,
) {
  return request<InteractionMessageDto>(
    `/interaction-rooms/${roomId}/messages/${messageId}`,
    getAccessToken,
    { method: "DELETE" },
  );
}

export function toggleInteractionReaction(
  roomId: string,
  messageId: string,
  code: string,
  getAccessToken?: () => string | undefined,
) {
  return request<InteractionMessageDto>(
    `/interaction-rooms/${roomId}/messages/${messageId}/reactions`,
    getAccessToken,
    { method: "POST", body: JSON.stringify({ code }) },
  );
}

export function pinInteractionMessage(
  roomId: string,
  messageId: string,
  pinned: boolean,
  getAccessToken?: () => string | undefined,
) {
  return request<InteractionMessageDto>(
    `/interaction-rooms/${roomId}/messages/${messageId}/pin`,
    getAccessToken,
    { method: pinned ? "POST" : "DELETE" },
  );
}

export function markInteractionRoomRead(roomId: string, getAccessToken?: () => string | undefined) {
  return request<{ room_id: string }>(`/interaction-rooms/${roomId}/read`, getAccessToken, {
    method: "POST",
  });
}

export function listInteractionAttachments(roomId: string, getAccessToken?: () => string | undefined) {
  return request<{ items: InteractionAttachmentDto[] }>(
    `/interaction-rooms/${roomId}/attachments`,
    getAccessToken,
  );
}

export function uploadInteractionAttachment(
  roomId: string,
  messageId: string,
  file: File,
  getAccessToken?: () => string | undefined,
) {
  const body = new FormData();
  body.append("file", file, file.name);
  return fetch(
    `${TRANSFORMOMETRO_API_BASE}/interaction-rooms/${roomId}/messages/${messageId}/attachments`,
    {
      method: "POST",
      headers: buildAuthHeaders(getAccessToken),
      body,
    },
  ).then((response) => parseApiEnvelope<InteractionAttachmentDto>(response));
}

export async function downloadInteractionAttachment(
  roomId: string,
  attachmentId: string,
  getAccessToken?: () => string | undefined,
) {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/interaction-rooms/${roomId}/attachments/${attachmentId}`,
    { headers: buildAuthHeaders(getAccessToken) },
  );
  if (!response.ok) {
    throw new Error("Não foi possível baixar o arquivo.");
  }
  return response.blob();
}

export function deleteInteractionAttachment(
  roomId: string,
  attachmentId: string,
  getAccessToken?: () => string | undefined,
) {
  return request<{ id: string }>(
    `/interaction-rooms/${roomId}/attachments/${attachmentId}`,
    getAccessToken,
    { method: "DELETE" },
  );
}
