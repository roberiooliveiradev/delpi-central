import type { NcAttachmentType, NcAttachment } from "../api/audit5sApi";
import { getAccessToken } from "../api/httpClient";

const attachmentPreviewCache = new Map<string, string>();

export function ncAttachmentFileUrl(ncId: string, attachmentId: string): string {
  return `/apps/api-delpi/quality/audit-5s/nonconformities/${ncId}/attachments/${attachmentId}/file`;
}

export async function fetchNcAttachmentPreviewUrl(
  ncId: string,
  attachment: NcAttachment,
): Promise<string> {
  const cacheKey = attachment.id;
  const cached = attachmentPreviewCache.get(cacheKey);
  if (cached) return cached;

  const token = getAccessToken();
  const response = await fetch(ncAttachmentFileUrl(ncId, attachment.id), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error("Não foi possível carregar a evidência.");
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  attachmentPreviewCache.set(cacheKey, objectUrl);
  return objectUrl;
}

export function groupAttachmentsByResponse(
  attachments: NcAttachment[],
): Record<string, Partial<Record<NcAttachmentType, NcAttachment>>> {
  const grouped: Record<string, Partial<Record<NcAttachmentType, NcAttachment>>> = {};
  for (const item of attachments) {
    if (!grouped[item.nonconformity_id]) {
      grouped[item.nonconformity_id] = {};
    }
    grouped[item.nonconformity_id][item.attachment_type] = item;
  }
  return grouped;
}

export function hasNcEvidence(
  ncId: string | undefined,
  attachmentsByNcId: Record<string, Partial<Record<NcAttachmentType, NcAttachment>>>,
): { before: boolean; after: boolean } {
  if (!ncId) return { before: false, after: false };
  const slots = attachmentsByNcId[ncId] ?? {};
  return {
    before: Boolean(slots.before),
    after: Boolean(slots.after),
  };
}
