import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import {
  commercialApiUrl,
  httpDelete,
  httpGet,
  httpGetBlob,
  httpPostFormData,
} from "./httpClient";

export type CommercialAttachmentDto = {
  id: string;
  owner_type: string;
  owner_id: string;
  file_name: string;
  content_type: string;
  byte_size: number;
  uploaded_by_user_id: string;
  created_at?: string | null;
};

export async function listTaskAttachments(
  taskId: string,
  signal?: AbortSignal,
): Promise<CommercialAttachmentDto[]> {
  const params = new URLSearchParams({
    owner_type: "task",
    owner_id: taskId,
  });
  const response = await httpGet<ApiSuccessResponse<{ items?: CommercialAttachmentDto[] }>>(
    `${commercialApiUrl("/attachments")}?${params.toString()}`,
    { signal },
  );
  const data = unwrapEnvelope(response, "Erro ao listar anexos.");
  return data.items ?? [];
}

export async function uploadTaskAttachment(
  taskId: string,
  file: File,
  signal?: AbortSignal,
): Promise<CommercialAttachmentDto> {
  const formData = new FormData();
  formData.set("owner_type", "task");
  formData.set("owner_id", taskId);
  formData.set("file", file);
  const response = await httpPostFormData<ApiSuccessResponse<CommercialAttachmentDto>>(
    commercialApiUrl("/attachments"),
    formData,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao enviar anexo.");
}

export async function deleteAttachment(
  attachmentId: string,
  signal?: AbortSignal,
): Promise<void> {
  await httpDelete(
    commercialApiUrl(`/attachments/${encodeURIComponent(attachmentId)}`),
    { signal },
  );
}

export async function downloadAttachmentBlob(
  attachmentId: string,
  signal?: AbortSignal,
): Promise<Blob> {
  return httpGetBlob(
    commercialApiUrl(`/attachments/${encodeURIComponent(attachmentId)}/content`),
    { signal },
  );
}
