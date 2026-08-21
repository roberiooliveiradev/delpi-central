/**
 * Cliente HTTP da sala de interação — só commercial-api
 * (`/interaction-rooms` + `/attachments` com owner_type=room_message).
 * Proibido api-delpi / Core no MFE.
 */
import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import {
  commercialApiUrl,
  httpDelete,
  httpGet,
  httpGetBlob,
  httpPatch,
  httpPost,
  httpPostFormData,
  httpPut,
} from "./httpClient";
import type { CommercialAttachmentDto } from "./attachmentsApi";
import { deleteAttachment } from "./attachmentsApi";
import type { CommercialTaskDto } from "./worklistApi";

export const INTERACTION_ROOMS_API_BASE = "/interaction-rooms";
export const ROOM_MESSAGE_OWNER_TYPE = "room_message";

export type InteractionRoomKind = "entity" | "process" | "wall" | string;
export type InteractionInboxFilter =
  | "all"
  | "unread"
  | "mentioned"
  | "process"
  | "wall"
  | string;

export type InteractionRoomDto = {
  id: string;
  kind: InteractionRoomKind;
  title: string;
  entity_type?: string | null;
  entity_key?: string | null;
  group_id?: string | null;
  created_by_user_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  deleted_at?: string | null;
};

export type InteractionRoomInboxItemDto = InteractionRoomDto & {
  unread_count: number;
  mentioned: boolean;
  last_message_preview?: string | null;
  last_message_at?: string | null;
  last_author_user_id?: string | null;
  customer_code?: string | null;
  customer_store?: string | null;
  customer_name?: string | null;
};

export type InteractionRoomMemberDto = {
  id: string;
  room_id: string;
  user_id: string;
  role: string;
  last_read_at?: string | null;
  muted?: boolean;
  created_at?: string | null;
};

export type InteractionMentionDto = {
  id: string;
  message_id: string;
  mention_kind: string;
  ref: Record<string, unknown>;
  label: string;
};

export type InteractionReactionDto = {
  message_id: string;
  user_id: string;
  code: string;
  created_at?: string | null;
};

export type InteractionPinDto = {
  id: string;
  room_id: string;
  message_id: string;
  pinned_by_user_id: string;
  created_at?: string | null;
};

export type InteractionRoomSharedItemKind = "file" | "link" | string;

export type InteractionRoomSharedItemDto = {
  id: string;
  kind: InteractionRoomSharedItemKind;
  title: string;
  subtitle?: string | null;
  shared_at?: string | null;
  shared_by?: string | null;
  message_id: string;
  attachment_id?: string | null;
  href?: string | null;
};

export type InteractionMessageDto = {
  id: string;
  room_id: string;
  parent_id?: string | null;
  author_user_id?: string | null;
  message_kind: string;
  body_text: string;
  edited_at?: string | null;
  deleted_at?: string | null;
  created_at?: string | null;
  mentions?: InteractionMentionDto[];
  reactions?: InteractionReactionDto[];
};

export type InteractionMentionSuggestItemDto = {
  id?: string;
  kind: string;
  label: string;
  subtitle?: string;
  ref?: Record<string, unknown>;
};

export type InteractionEntityPreviewDto = {
  kind: string;
  accessible: boolean;
  label: string;
  subtitle?: string;
  hrefStrategy?: string;
  ref?: Record<string, unknown>;
  fields?: Record<string, unknown>;
};

export type ResolveInteractionRoomInput = {
  kind: InteractionRoomKind;
  entity_type?: string | null;
  entity_key?: string | null;
  group_id?: string | null;
  title?: string | null;
};

export type PostInteractionMessageInput = {
  body_text: string;
  message_kind?: string;
  parent_id?: string | null;
  mentions?: Array<{
    kind: string;
    ref: Record<string, unknown>;
    label: string;
  }>;
};

/** Path builders — unit-tested (EN paths, no api-delpi). */
export function interactionRoomsCollectionPath(): string {
  return INTERACTION_ROOMS_API_BASE;
}

export function interactionRoomPath(roomId: string): string {
  return `${INTERACTION_ROOMS_API_BASE}/${encodeURIComponent(roomId)}`;
}

export function interactionRoomResolvePath(): string {
  return `${INTERACTION_ROOMS_API_BASE}/resolve`;
}

export function interactionRoomMentionSuggestPath(): string {
  return `${INTERACTION_ROOMS_API_BASE}/mention-suggest`;
}

export function interactionRoomEntityPreviewPath(): string {
  return `${INTERACTION_ROOMS_API_BASE}/entity-preview`;
}

export function interactionRoomMembersPath(roomId: string): string {
  return `${interactionRoomPath(roomId)}/members`;
}

export function interactionRoomMemberPath(roomId: string, userId: string): string {
  return `${interactionRoomMembersPath(roomId)}/${encodeURIComponent(userId)}`;
}

export function interactionRoomReadPath(roomId: string): string {
  return `${interactionRoomPath(roomId)}/read`;
}

export function interactionRoomMessagesPath(roomId: string): string {
  return `${interactionRoomPath(roomId)}/messages`;
}

export function interactionRoomMessagePath(roomId: string, messageId: string): string {
  return `${interactionRoomMessagesPath(roomId)}/${encodeURIComponent(messageId)}`;
}

export function interactionRoomReactionPath(
  roomId: string,
  messageId: string,
  code: string,
): string {
  return `${interactionRoomMessagePath(roomId, messageId)}/reactions/${encodeURIComponent(code)}`;
}

export function interactionRoomMessageTasksPath(
  roomId: string,
  messageId: string,
): string {
  return `${interactionRoomMessagePath(roomId, messageId)}/tasks`;
}

export function interactionRoomPinsPath(roomId: string): string {
  return `${interactionRoomPath(roomId)}/pins`;
}

export function interactionRoomSharedItemsPath(roomId: string): string {
  return `${interactionRoomPath(roomId)}/shared-items`;
}

export function interactionRoomMessagePinPath(
  roomId: string,
  messageId: string,
): string {
  return `${interactionRoomMessagePath(roomId, messageId)}/pin`;
}

export function interactionRoomsUrl(path: string): string {
  return commercialApiUrl(path);
}

export async function listInteractionRooms(
  options?: {
    filter?: InteractionInboxFilter;
    q?: string | null;
    limit?: number;
    signal?: AbortSignal;
  },
): Promise<InteractionRoomInboxItemDto[]> {
  const params = new URLSearchParams();
  if (options?.filter) params.set("filter", options.filter);
  if (options?.q) params.set("q", options.q);
  if (options?.limit != null) params.set("limit", String(options.limit));
  const query = params.toString();
  const response = await httpGet<
    ApiSuccessResponse<{ items?: InteractionRoomInboxItemDto[] }>
  >(
    `${interactionRoomsUrl(interactionRoomsCollectionPath())}${query ? `?${query}` : ""}`,
    { signal: options?.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao listar salas.");
  return data.items ?? [];
}

export async function resolveInteractionRoom(
  input: ResolveInteractionRoomInput,
  signal?: AbortSignal,
): Promise<InteractionRoomDto> {
  const response = await httpPost<ApiSuccessResponse<InteractionRoomDto>>(
    interactionRoomsUrl(interactionRoomResolvePath()),
    {
      kind: input.kind,
      entity_type: input.entity_type ?? undefined,
      entity_key: input.entity_key ?? undefined,
      group_id: input.group_id ?? undefined,
      title: input.title ?? undefined,
    },
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao abrir a sala.");
}

export async function getInteractionRoom(
  roomId: string,
  signal?: AbortSignal,
): Promise<InteractionRoomDto> {
  const response = await httpGet<ApiSuccessResponse<InteractionRoomDto>>(
    interactionRoomsUrl(interactionRoomPath(roomId)),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar a sala.");
}

export async function listInteractionRoomMembers(
  roomId: string,
  signal?: AbortSignal,
): Promise<InteractionRoomMemberDto[]> {
  const response = await httpGet<
    ApiSuccessResponse<{ items?: InteractionRoomMemberDto[] }>
  >(interactionRoomsUrl(interactionRoomMembersPath(roomId)), { signal });
  const data = unwrapEnvelope(response, "Erro ao listar membros.");
  return data.items ?? [];
}

export async function addInteractionRoomMember(
  roomId: string,
  userId: string,
  role?: string,
  signal?: AbortSignal,
): Promise<InteractionRoomMemberDto> {
  const response = await httpPost<ApiSuccessResponse<InteractionRoomMemberDto>>(
    interactionRoomsUrl(interactionRoomMembersPath(roomId)),
    { user_id: userId, role: role ?? "member" },
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao adicionar membro.");
}

export async function removeInteractionRoomMember(
  roomId: string,
  userId: string,
  signal?: AbortSignal,
): Promise<void> {
  await httpDelete(interactionRoomsUrl(interactionRoomMemberPath(roomId, userId)), {
    signal,
  });
}

export async function markInteractionRoomRead(
  roomId: string,
  signal?: AbortSignal,
): Promise<InteractionRoomMemberDto> {
  const response = await httpPost<ApiSuccessResponse<InteractionRoomMemberDto>>(
    interactionRoomsUrl(interactionRoomReadPath(roomId)),
    {},
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao marcar leitura.");
}

export async function listInteractionMessages(
  roomId: string,
  options?: {
    limit?: number;
    beforeId?: string | null;
    beforeCreatedAt?: string | null;
    q?: string | null;
    signal?: AbortSignal;
  },
): Promise<InteractionMessageDto[]> {
  const params = new URLSearchParams();
  if (options?.limit != null) params.set("limit", String(options.limit));
  if (options?.beforeId) params.set("before_id", options.beforeId);
  if (options?.beforeCreatedAt) params.set("before_created_at", options.beforeCreatedAt);
  if (options?.q) params.set("q", options.q);
  const query = params.toString();
  const response = await httpGet<
    ApiSuccessResponse<{ items?: InteractionMessageDto[] }>
  >(
    `${interactionRoomsUrl(interactionRoomMessagesPath(roomId))}${query ? `?${query}` : ""}`,
    { signal: options?.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao listar mensagens.");
  return data.items ?? [];
}

export async function postInteractionMessage(
  roomId: string,
  input: PostInteractionMessageInput,
  signal?: AbortSignal,
): Promise<InteractionMessageDto> {
  const response = await httpPost<ApiSuccessResponse<InteractionMessageDto>>(
    interactionRoomsUrl(interactionRoomMessagesPath(roomId)),
    {
      body_text: input.body_text,
      message_kind: input.message_kind ?? "text",
      parent_id: input.parent_id ?? undefined,
      mentions: input.mentions ?? [],
    },
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao enviar mensagem.");
}

export type UpdateInteractionMessageInput = {
  body_text: string;
  /** When provided (incl. empty), replaces mentions on the server. */
  mentions?: PostInteractionMessageInput["mentions"];
};

export async function updateInteractionMessage(
  roomId: string,
  messageId: string,
  input: UpdateInteractionMessageInput,
  signal?: AbortSignal,
): Promise<InteractionMessageDto> {
  const payload: Record<string, unknown> = {
    body_text: input.body_text,
  };
  if (input.mentions !== undefined) {
    payload.mentions = input.mentions;
  }
  const response = await httpPatch<ApiSuccessResponse<InteractionMessageDto>>(
    interactionRoomsUrl(interactionRoomMessagePath(roomId, messageId)),
    payload,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao atualizar mensagem.");
}

export async function deleteInteractionRoom(
  roomId: string,
  signal?: AbortSignal,
): Promise<InteractionRoomDto> {
  const response = await httpDelete<ApiSuccessResponse<InteractionRoomDto>>(
    interactionRoomsUrl(interactionRoomPath(roomId)),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao excluir a conversa.");
}

export async function deleteInteractionMessage(
  roomId: string,
  messageId: string,
  signal?: AbortSignal,
): Promise<InteractionMessageDto> {
  const response = await httpDelete<ApiSuccessResponse<InteractionMessageDto>>(
    interactionRoomsUrl(interactionRoomMessagePath(roomId, messageId)),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao excluir mensagem.");
}

export async function createTaskFromInteractionMessage(
  roomId: string,
  messageId: string,
  options?: { description?: string | null; signal?: AbortSignal },
): Promise<{
  task: CommercialTaskDto;
  task_ref_message: InteractionMessageDto;
}> {
  const response = await httpPost<
    ApiSuccessResponse<{
      task?: CommercialTaskDto;
      task_ref_message?: InteractionMessageDto;
    }>
  >(
    interactionRoomsUrl(interactionRoomMessageTasksPath(roomId, messageId)),
    {
      description: options?.description?.trim() || undefined,
    },
    { signal: options?.signal },
  );
  const data = unwrapEnvelope(
    response,
    "Erro ao criar tarefa a partir da mensagem.",
  );
  if (!data.task || !data.task_ref_message) {
    throw new Error("Erro ao criar tarefa a partir da mensagem.");
  }
  return {
    task: data.task,
    task_ref_message: data.task_ref_message,
  };
}

export async function listInteractionRoomPins(
  roomId: string,
  signal?: AbortSignal,
): Promise<InteractionPinDto[]> {
  const response = await httpGet<
    ApiSuccessResponse<{ items?: InteractionPinDto[] }>
  >(interactionRoomsUrl(interactionRoomPinsPath(roomId)), { signal });
  const data = unwrapEnvelope(response, "Erro ao listar pins.");
  return data.items ?? [];
}

export async function listRoomSharedItems(
  roomId: string,
  options?: {
    kind?: "all" | "file" | "link" | string;
    q?: string | null;
    signal?: AbortSignal;
  },
): Promise<InteractionRoomSharedItemDto[]> {
  const params = new URLSearchParams();
  if (options?.kind) params.set("kind", options.kind);
  if (options?.q) params.set("q", options.q);
  const query = params.toString();
  const response = await httpGet<
    ApiSuccessResponse<{ items?: InteractionRoomSharedItemDto[] }>
  >(
    `${interactionRoomsUrl(interactionRoomSharedItemsPath(roomId))}${
      query ? `?${query}` : ""
    }`,
    { signal: options?.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao listar itens compartilhados.");
  return data.items ?? [];
}

export async function pinInteractionMessage(
  roomId: string,
  messageId: string,
  signal?: AbortSignal,
): Promise<InteractionPinDto> {
  const response = await httpPost<ApiSuccessResponse<InteractionPinDto>>(
    interactionRoomsUrl(interactionRoomMessagePinPath(roomId, messageId)),
    {},
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao fixar mensagem.");
}

export async function unpinInteractionMessage(
  roomId: string,
  messageId: string,
  signal?: AbortSignal,
): Promise<void> {
  await httpDelete(
    interactionRoomsUrl(interactionRoomMessagePinPath(roomId, messageId)),
    { signal },
  );
}

export async function setInteractionMessageReaction(
  roomId: string,
  messageId: string,
  code: string,
  signal?: AbortSignal,
): Promise<InteractionReactionDto> {
  const response = await httpPut<ApiSuccessResponse<InteractionReactionDto>>(
    interactionRoomsUrl(interactionRoomReactionPath(roomId, messageId, code)),
    {},
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao reagir.");
}

export async function clearInteractionMessageReaction(
  roomId: string,
  messageId: string,
  code: string,
  signal?: AbortSignal,
): Promise<void> {
  await httpDelete(
    interactionRoomsUrl(interactionRoomReactionPath(roomId, messageId, code)),
    { signal },
  );
}

export async function suggestInteractionMentions(
  options: {
    q: string;
    kinds?: string[];
    limit?: number;
    signal?: AbortSignal;
  },
): Promise<InteractionMentionSuggestItemDto[]> {
  const params = new URLSearchParams();
  params.set("q", options.q ?? "");
  if (options.kinds?.length) params.set("kinds", options.kinds.join(","));
  if (options.limit != null) params.set("limit", String(options.limit));
  const response = await httpGet<
    ApiSuccessResponse<{ items?: InteractionMentionSuggestItemDto[] }>
  >(
    `${interactionRoomsUrl(interactionRoomMentionSuggestPath())}?${params.toString()}`,
    { signal: options.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao sugerir menções.");
  return data.items ?? [];
}

export async function previewInteractionEntity(
  kind: string,
  ref: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<InteractionEntityPreviewDto> {
  const params = new URLSearchParams({
    kind,
    ref: JSON.stringify(ref ?? {}),
  });
  const response = await httpGet<ApiSuccessResponse<InteractionEntityPreviewDto>>(
    `${interactionRoomsUrl(interactionRoomEntityPreviewPath())}?${params.toString()}`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar a prévia.");
}

export async function listRoomMessageAttachments(
  messageId: string,
  signal?: AbortSignal,
): Promise<CommercialAttachmentDto[]> {
  const params = new URLSearchParams({
    owner_type: ROOM_MESSAGE_OWNER_TYPE,
    owner_id: messageId,
  });
  const response = await httpGet<
    ApiSuccessResponse<{ items?: CommercialAttachmentDto[] }>
  >(`${commercialApiUrl("/attachments")}?${params.toString()}`, { signal });
  const data = unwrapEnvelope(response, "Erro ao listar anexos da mensagem.");
  return data.items ?? [];
}

export async function uploadRoomMessageAttachment(
  messageId: string,
  file: File,
  signal?: AbortSignal,
): Promise<CommercialAttachmentDto> {
  const formData = new FormData();
  formData.set("owner_type", ROOM_MESSAGE_OWNER_TYPE);
  formData.set("owner_id", messageId);
  formData.set("file", file);
  const response = await httpPostFormData<ApiSuccessResponse<CommercialAttachmentDto>>(
    commercialApiUrl("/attachments"),
    formData,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao enviar anexo da mensagem.");
}

export async function downloadRoomMessageAttachmentBlob(
  attachmentId: string,
  signal?: AbortSignal,
): Promise<Blob> {
  return httpGetBlob(
    commercialApiUrl(`/attachments/${encodeURIComponent(attachmentId)}/content`),
    { signal },
  );
}

export async function deleteRoomMessageAttachment(
  attachmentId: string,
  signal?: AbortSignal,
): Promise<void> {
  await deleteAttachment(attachmentId, signal);
}
