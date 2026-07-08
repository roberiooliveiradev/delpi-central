import type { ResponseAttachment } from "../api/audit5sApi";
import { getAccessToken } from "../api/httpClient";

const responseAttachmentPreviewCache = new Map<string, string>();

export function responseAttachmentFileUrl(
  auditId: string,
  criterionId: string,
  attachmentId: string,
): string {
  return `/apps/api-delpi/quality/audit-5s/audits/${auditId}/responses/${criterionId}/attachments/${attachmentId}/file`;
}

export async function fetchResponseAttachmentPreviewUrl(
  auditId: string,
  criterionId: string,
  attachment: ResponseAttachment,
): Promise<string> {
  const cacheKey = attachment.id;
  const cached = responseAttachmentPreviewCache.get(cacheKey);
  if (cached) return cached;

  const token = getAccessToken();
  const response = await fetch(
    responseAttachmentFileUrl(auditId, criterionId, attachment.id),
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  );
  if (!response.ok) {
    throw new Error("Não foi possível carregar a foto do critério.");
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  responseAttachmentPreviewCache.set(cacheKey, objectUrl);
  return objectUrl;
}

export function clearResponseAttachmentPreviewCache(attachmentId?: string) {
  if (!attachmentId) {
    for (const url of responseAttachmentPreviewCache.values()) {
      URL.revokeObjectURL(url);
    }
    responseAttachmentPreviewCache.clear();
    return;
  }
  const url = responseAttachmentPreviewCache.get(attachmentId);
  if (url) {
    URL.revokeObjectURL(url);
    responseAttachmentPreviewCache.delete(attachmentId);
  }
}
