/** Paths de mídia/anexo retornados pela API → URL absoluta no gateway. */

const GATEWAY_PREFIX = "/apps/api-delpi";

export function toGatewayAssetUrl(pathOrUrl: string | null | undefined): string {
  const raw = (pathOrUrl || "").trim();
  if (!raw) return "";
  if (/^https?:\/\//i.test(raw)) return raw;
  if (raw.startsWith("/apps/")) return raw;
  if (raw.startsWith("/guias-procedimentos/")) {
    return `${GATEWAY_PREFIX}${raw}`;
  }
  if (raw.startsWith("/")) {
    return `${GATEWAY_PREFIX}${raw}`;
  }
  return raw;
}

export function mediaContentUrl(mediaId: string): string {
  return `${GATEWAY_PREFIX}/guias-procedimentos/media/${encodeURIComponent(mediaId)}/file`;
}

export function attachmentDownloadUrl(attachmentId: string): string {
  return `${GATEWAY_PREFIX}/guias-procedimentos/attachments/${encodeURIComponent(attachmentId)}/file`;
}

export function isProtectedGuideMediaSrc(src: string): boolean {
  return /^\/(?:apps\/api-delpi\/)?guias-procedimentos\/media\/[0-9a-fA-F-]{36}\/file$/.test(
    src.trim(),
  );
}

export function isProtectedGuideAttachmentHref(href: string): boolean {
  return /^\/(?:apps\/api-delpi\/)?guias-procedimentos\/attachments\/[0-9a-fA-F-]{36}\/file$/.test(
    href.trim(),
  );
}
