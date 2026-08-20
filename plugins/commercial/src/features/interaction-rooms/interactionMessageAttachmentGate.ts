import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

const RAW_HTML_PROBE = /<[a-zA-Z!/?]/;
const ALLOWED_INLINE =
  /<\/?u>|<span\s+style="font-size:\s*\d+px"\s*>|<\/span>/gi;

/** Alinhado à política da commercial-api (markdown + inline permitido). */
export function interactionMessageLooksLikeRawHtml(body: string): boolean {
  const text = String(body ?? "");
  if (!text.includes("<")) return false;
  const cleaned = text.replace(ALLOWED_INLINE, "");
  return RAW_HTML_PROBE.test(cleaned);
}

export function formatAttachTooMany(max = INTERACTION_ROOMS_CONTENT.attachMaxCount): string {
  return INTERACTION_ROOMS_CONTENT.attachTooMany.replace("{max}", String(max));
}

export function formatAttachTooLarge(
  maxBytes = INTERACTION_ROOMS_CONTENT.attachMaxBytes,
): string {
  const maxMb = Math.max(1, Math.floor(maxBytes / (1024 * 1024)));
  return INTERACTION_ROOMS_CONTENT.attachTooLarge.replace("{maxMb}", String(maxMb));
}

export type PendingAttachmentGate = {
  ok: true;
  files: File[];
} | {
  ok: false;
  message: string;
};

/** Recusa >10 arquivos ou >20 MB antes do POST/upload. */
export function gatePendingAttachments(
  currentCount: number,
  incoming: readonly File[],
  options?: {
    maxCount?: number;
    maxBytes?: number;
  },
): PendingAttachmentGate {
  const maxCount = options?.maxCount ?? INTERACTION_ROOMS_CONTENT.attachMaxCount;
  const maxBytes = options?.maxBytes ?? INTERACTION_ROOMS_CONTENT.attachMaxBytes;
  if (!incoming.length) return { ok: true, files: [] };
  const room = Math.max(0, maxCount - currentCount);
  if (room <= 0 || incoming.length > room) {
    return { ok: false, message: formatAttachTooMany(maxCount) };
  }
  for (const file of incoming) {
    if (file.size > maxBytes) {
      return { ok: false, message: formatAttachTooLarge(maxBytes) };
    }
  }
  return { ok: true, files: [...incoming] };
}
