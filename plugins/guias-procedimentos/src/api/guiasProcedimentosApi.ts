import {
  httpGet,
  httpGetBlob,
  httpPost,
  httpPostFormWithProgress,
  httpPut,
  type UploadProgressCallback,
} from "./httpClient";
import {
  type ApiSuccessResponse,
  unwrapApiDelpiEnvelope,
} from "./types";
import {
  attachmentDownloadUrl,
  mediaContentUrl,
  toGatewayAssetUrl,
} from "../utils/guideAssetUrls.ts";

const API_BASE = "/apps/api-delpi/guias-procedimentos";

export type MediaKind = "image" | "video_file" | "video_external";

/** Contrato HTTP (snake_case) — espelha media_payload / attachment_payload. */
export type ApiProcedureMedia = {
  id: string;
  procedure_id: string;
  media_kind: MediaKind;
  title: string;
  alt_text: string;
  original_filename: string | null;
  stored_name: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  storage_subdir: string | null;
  external_url: string | null;
  external_provider: string | null;
  order_index: number;
  archived_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  created_by_user_id?: string | null;
  created_by_name?: string | null;
  updated_by_user_id?: string | null;
  updated_by_name?: string | null;
  /** Path relativo da API quando há arquivo local. */
  file_path?: string | null;
};

export type ApiProcedureAttachment = {
  id: string;
  procedure_id: string;
  title: string;
  original_filename: string | null;
  stored_name: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  order_index: number;
  archived_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  created_by_user_id?: string | null;
  created_by_name?: string | null;
  updated_by_user_id?: string | null;
  updated_by_name?: string | null;
  download_path?: string | null;
};

/** Modelo interno do MFE com URLs absolutas de gateway. */
export type ProcedureMedia = ApiProcedureMedia & {
  content_url: string | null;
};

export type ProcedureAttachment = ApiProcedureAttachment & {
  download_url: string;
};

export type MediaMetadataPayload = {
  title: string;
  alt_text: string;
  order_index: number;
};

export type AttachmentMetadataPayload = {
  title: string;
  order_index: number;
};

export type ExternalVideoPayload = {
  url: string;
  title: string;
  order_index: number;
};

export type MediaUploadFields = {
  title?: string;
  alt_text?: string;
  order_index?: number;
};

export type AttachmentUploadFields = {
  title?: string;
  order_index?: number;
};

function mapMedia(row: ApiProcedureMedia): ProcedureMedia {
  const content_url =
    row.media_kind === "video_external"
      ? row.external_url
      : toGatewayAssetUrl(row.file_path) || mediaContentUrl(row.id);
  return { ...row, content_url };
}

function mapAttachment(row: ApiProcedureAttachment): ProcedureAttachment {
  return {
    ...row,
    download_url:
      toGatewayAssetUrl(row.download_path) || attachmentDownloadUrl(row.id),
  };
}

export type ProcedureStatus = "draft" | "published" | "archived";

export type ApiDepartmentListItem = {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
  order_index: number;
  procedure_count: number;
  active?: boolean;
};

export type ApiProcedureSummary = {
  id: string;
  title: string;
  slug: string;
  summary: string;
  reading_time_minutes: number | null;
  order_index: number;
};

export type ApiDepartmentDetail = ApiDepartmentListItem & {
  procedures: ApiProcedureSummary[];
};

export type ApiProcedureDetail = {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content_html: string;
  reading_time_minutes: number | null;
  order_index: number;
  published_at: string | null;
  updated_at: string | null;
  department: {
    id: string;
    name: string;
    slug: string;
    icon: string;
  };
};

export type ApiAdminDepartment = ApiDepartmentListItem & {
  active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  created_by_user_id?: string | null;
  created_by_name?: string | null;
  updated_by_user_id?: string | null;
  updated_by_name?: string | null;
};

export type ApiAdminProcedureListItem = {
  id: string;
  title: string;
  slug: string;
  summary: string;
  status: ProcedureStatus;
  reading_time_minutes: number | null;
  order_index: number;
  published_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  department: {
    id: string;
    name: string;
    slug: string;
    icon: string;
    active: boolean;
  };
};

export type ApiAdminProcedureDetail = ApiAdminProcedureListItem & {
  content_html: string;
  created_by_user_id?: string | null;
  created_by_name?: string | null;
  updated_by_user_id?: string | null;
  updated_by_name?: string | null;
  published_by_user_id?: string | null;
  published_by_name?: string | null;
  archived_at?: string | null;
  archived_by_user_id?: string | null;
  archived_by_name?: string | null;
};

export type DepartmentPayload = {
  name: string;
  slug: string;
  description: string;
  icon: string;
  active: boolean;
  order_index: number;
};

export type ProcedurePayload = {
  department_id: string;
  title: string;
  slug: string;
  summary: string;
  content_html: string;
  reading_time_minutes: number | null;
  order_index: number;
};

async function unwrapGet<T>(url: string, fallback: string): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(url);
  return unwrapApiDelpiEnvelope(response, fallback);
}

async function unwrapPost<T>(
  url: string,
  body: unknown | undefined,
  fallback: string,
): Promise<T> {
  const response = await httpPost<ApiSuccessResponse<T>>(url, body);
  return unwrapApiDelpiEnvelope(response, fallback);
}

async function unwrapPut<T>(
  url: string,
  body: unknown,
  fallback: string,
): Promise<T> {
  const response = await httpPut<ApiSuccessResponse<T>>(url, body);
  return unwrapApiDelpiEnvelope(response, fallback);
}

export function listPublicDepartments(signal?: AbortSignal) {
  return unwrapGet<ApiDepartmentListItem[]>(
    `${API_BASE}/departments`,
    "Não foi possível carregar os departamentos.",
  ).catch((error) => {
    if (signal?.aborted) throw error;
    throw error;
  });
}

export function getPublicDepartment(slug: string) {
  return unwrapGet<ApiDepartmentDetail>(
    `${API_BASE}/departments/${encodeURIComponent(slug)}`,
    "Departamento não encontrado.",
  );
}

export function getPublicProcedure(slug: string) {
  return unwrapGet<ApiProcedureDetail>(
    `${API_BASE}/procedures/${encodeURIComponent(slug)}`,
    "Procedimento não encontrado.",
  );
}

export function listAdminDepartments() {
  return unwrapGet<ApiAdminDepartment[]>(
    `${API_BASE}/admin/departments`,
    "Não foi possível carregar os departamentos.",
  );
}

export function getAdminDepartment(id: string) {
  return unwrapGet<ApiAdminDepartment>(
    `${API_BASE}/admin/departments/${encodeURIComponent(id)}`,
    "Departamento não encontrado.",
  );
}

export function createAdminDepartment(payload: DepartmentPayload) {
  return unwrapPost<ApiAdminDepartment>(
    `${API_BASE}/admin/departments`,
    payload,
    "Não foi possível criar o departamento.",
  );
}

export function updateAdminDepartment(id: string, payload: DepartmentPayload) {
  return unwrapPut<ApiAdminDepartment>(
    `${API_BASE}/admin/departments/${encodeURIComponent(id)}`,
    payload,
    "Não foi possível atualizar o departamento.",
  );
}

export function listAdminProcedures(params?: {
  department_id?: string;
  status?: string;
  q?: string;
}) {
  const search = new URLSearchParams();
  if (params?.department_id) search.set("department_id", params.department_id);
  if (params?.status) search.set("status", params.status);
  if (params?.q) search.set("q", params.q);
  const qs = search.toString();
  return unwrapGet<ApiAdminProcedureListItem[]>(
    `${API_BASE}/admin/procedures${qs ? `?${qs}` : ""}`,
    "Não foi possível carregar os procedimentos.",
  );
}

export function getAdminProcedure(id: string) {
  return unwrapGet<ApiAdminProcedureDetail>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(id)}`,
    "Procedimento não encontrado.",
  );
}

export function createAdminProcedure(payload: ProcedurePayload) {
  return unwrapPost<ApiAdminProcedureDetail>(
    `${API_BASE}/admin/procedures`,
    payload,
    "Não foi possível criar o procedimento.",
  );
}

export function updateAdminProcedure(id: string, payload: ProcedurePayload) {
  return unwrapPut<ApiAdminProcedureDetail>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(id)}`,
    payload,
    "Não foi possível atualizar o procedimento.",
  );
}

export function publishAdminProcedure(id: string) {
  return unwrapPost<ApiAdminProcedureDetail>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(id)}/publish`,
    undefined,
    "Não foi possível publicar o procedimento.",
  );
}

export function unpublishAdminProcedure(id: string) {
  return unwrapPost<ApiAdminProcedureDetail>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(id)}/unpublish`,
    undefined,
    "Não foi possível despublicar o procedimento.",
  );
}

export function archiveAdminProcedure(id: string) {
  return unwrapPost<ApiAdminProcedureDetail>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(id)}/archive`,
    undefined,
    "Não foi possível arquivar o procedimento.",
  );
}

export function restoreAdminProcedure(id: string) {
  return unwrapPost<ApiAdminProcedureDetail>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(id)}/restore`,
    undefined,
    "Não foi possível restaurar o procedimento.",
  );
}

async function unwrapPostForm<T>(
  url: string,
  formData: FormData,
  fallback: string,
  onProgress?: UploadProgressCallback,
): Promise<T> {
  const response = await httpPostFormWithProgress<ApiSuccessResponse<T>>(
    url,
    formData,
    { onProgress },
  );
  return unwrapApiDelpiEnvelope(response, fallback);
}

export async function listAdminProcedureMedia(procedureId: string) {
  const rows = await unwrapGet<ApiProcedureMedia[]>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(procedureId)}/media`,
    "Não foi possível carregar as mídias.",
  );
  return rows.map(mapMedia);
}

export async function listAdminProcedureAttachments(procedureId: string) {
  const rows = await unwrapGet<ApiProcedureAttachment[]>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(procedureId)}/attachments`,
    "Não foi possível carregar os anexos.",
  );
  return rows.map(mapAttachment);
}

export async function listReadableProcedureMedia(procedureId: string) {
  const rows = await unwrapGet<ApiProcedureMedia[]>(
    `${API_BASE}/procedures/${encodeURIComponent(procedureId)}/media`,
    "Não foi possível carregar as mídias.",
  );
  return rows.map(mapMedia);
}

export async function listReadableProcedureAttachments(procedureId: string) {
  const rows = await unwrapGet<ApiProcedureAttachment[]>(
    `${API_BASE}/procedures/${encodeURIComponent(procedureId)}/attachments`,
    "Não foi possível carregar os anexos.",
  );
  return rows.map(mapAttachment);
}

export function uploadProcedureImage(
  procedureId: string,
  file: File,
  fields: MediaUploadFields = {},
  onProgress?: UploadProgressCallback,
) {
  const form = new FormData();
  form.append("file", file);
  if (fields.title != null) form.append("title", fields.title);
  if (fields.alt_text != null) form.append("alt_text", fields.alt_text);
  if (fields.order_index != null) {
    form.append("order_index", String(fields.order_index));
  }
  return unwrapPostForm<ApiProcedureMedia>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(procedureId)}/media/images`,
    form,
    "Não foi possível enviar a imagem.",
    onProgress,
  ).then(mapMedia);
}

export function uploadProcedureVideo(
  procedureId: string,
  file: File,
  fields: MediaUploadFields = {},
  onProgress?: UploadProgressCallback,
) {
  const form = new FormData();
  form.append("file", file);
  if (fields.title != null) form.append("title", fields.title);
  if (fields.order_index != null) {
    form.append("order_index", String(fields.order_index));
  }
  return unwrapPostForm<ApiProcedureMedia>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(procedureId)}/media/videos`,
    form,
    "Não foi possível enviar o vídeo.",
    onProgress,
  ).then(mapMedia);
}

export function createExternalVideo(
  procedureId: string,
  payload: ExternalVideoPayload,
) {
  return unwrapPost<ApiProcedureMedia>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(procedureId)}/media/external-videos`,
    payload,
    "Não foi possível cadastrar o vídeo externo.",
  ).then(mapMedia);
}

export function updateMediaMetadata(mediaId: string, payload: MediaMetadataPayload) {
  return unwrapPut<ApiProcedureMedia>(
    `${API_BASE}/admin/media/${encodeURIComponent(mediaId)}`,
    payload,
    "Não foi possível atualizar a mídia.",
  ).then(mapMedia);
}

export function archiveMedia(mediaId: string) {
  return unwrapPost<ApiProcedureMedia>(
    `${API_BASE}/admin/media/${encodeURIComponent(mediaId)}/archive`,
    undefined,
    "Não foi possível arquivar a mídia.",
  ).then(mapMedia);
}

export function uploadProcedureAttachment(
  procedureId: string,
  file: File,
  fields: AttachmentUploadFields = {},
  onProgress?: UploadProgressCallback,
) {
  const form = new FormData();
  form.append("file", file);
  if (fields.title != null) form.append("title", fields.title);
  if (fields.order_index != null) {
    form.append("order_index", String(fields.order_index));
  }
  return unwrapPostForm<ApiProcedureAttachment>(
    `${API_BASE}/admin/procedures/${encodeURIComponent(procedureId)}/attachments`,
    form,
    "Não foi possível enviar o anexo.",
    onProgress,
  ).then(mapAttachment);
}

export function updateAttachmentMetadata(
  attachmentId: string,
  payload: AttachmentMetadataPayload,
) {
  return unwrapPut<ApiProcedureAttachment>(
    `${API_BASE}/admin/attachments/${encodeURIComponent(attachmentId)}`,
    payload,
    "Não foi possível atualizar o anexo.",
  ).then(mapAttachment);
}

export function archiveAttachment(attachmentId: string) {
  return unwrapPost<ApiProcedureAttachment>(
    `${API_BASE}/admin/attachments/${encodeURIComponent(attachmentId)}/archive`,
    undefined,
    "Não foi possível arquivar o anexo.",
  ).then(mapAttachment);
}

export function getMediaContentUrl(mediaId: string) {
  return mediaContentUrl(mediaId);
}

export function getAttachmentDownloadUrl(attachmentId: string) {
  return attachmentDownloadUrl(attachmentId);
}

export async function downloadProtectedBlob(url: string, signal?: AbortSignal) {
  return httpGetBlob(url, { signal });
}

export async function triggerAuthenticatedDownload(
  url: string,
  filename: string,
) {
  const blob = await httpGetBlob(url);
  const objectUrl = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename || "download";
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}
