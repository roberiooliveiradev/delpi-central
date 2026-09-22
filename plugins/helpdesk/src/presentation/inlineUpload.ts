/** H12 — helpers for paste/attach → BFF Document → inline img in the compositor. */

const PENDING_ATTR = "data-attachment-pending";

export type UploadedInlineImage = {
  documentId: number;
  src: string;
  alt?: string;
};

export type PendingInlineImage = {
  pendingId: string;
  src: string;
  alt?: string;
};

export function attachmentPublicUrl(ticketId: string | number, documentId: number): string {
  return `/apps/helpdesk-api/tickets/${ticketId}/attachments/${documentId}`;
}

export function appendInlineImageHtml(
  current: string,
  image: { src: string; alt?: string; documentId?: number; pendingId?: string },
): string {
  const alt = escapeAttr(image.alt || "imagem");
  const src = escapeAttr(image.src);
  const idAttr =
    image.documentId != null
      ? ` data-attachment-id="${image.documentId}"`
      : image.pendingId
        ? ` ${PENDING_ATTR}="${escapeAttr(image.pendingId)}"`
        : "";
  const block = `<p><img src="${src}" alt="${alt}"${idAttr} /></p>`;
  const base = String(current || "").trim();
  if (!base || base === "<p></p>" || base === "<p><br></p>" || base === "<p><br/></p>") {
    return block;
  }
  return `${base}${block}`;
}

export function listPendingInlineIds(html: string): string[] {
  const ids: string[] = [];
  const seen = new Set<string>();
  const re = new RegExp(`${PENDING_ATTR}=["']([^"']+)["']`, "gi");
  let match: RegExpExecArray | null;
  while ((match = re.exec(String(html || "")))) {
    const id = match[1];
    if (!id || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

export function rewritePendingInlineImages(
  html: string,
  mapping: Record<string, { documentId: number; ticketId: string | number }>,
): string {
  let next = String(html || "");
  for (const [pendingId, target] of Object.entries(mapping)) {
    const src = attachmentPublicUrl(target.ticketId, target.documentId);
    const pendingRe = new RegExp(
      `<img\\b([^>]*\\b${PENDING_ATTR}=["']${escapeRegExp(pendingId)}["'][^>]*)/?>`,
      "gi",
    );
    next = next.replace(pendingRe, (_full, attrs: string) => {
      let cleaned = String(attrs)
        .replace(new RegExp(`\\s${PENDING_ATTR}=["'][^"']*["']`, "i"), "")
        .replace(/\ssrc=["'][^"']*["']/i, ` src="${escapeAttr(src)}"`);
      if (!/\sdata-attachment-id=/i.test(cleaned)) {
        cleaned += ` data-attachment-id="${target.documentId}"`;
      }
      if (!/\ssrc=/i.test(cleaned)) {
        cleaned = ` src="${escapeAttr(src)}"${cleaned}`;
      }
      return `<img${cleaned} />`;
    });
  }
  return next;
}

/**
 * BFF attachment URLs require Bearer — `<img src>` alone returns 401.
 * Composer may show a blob: preview; normalize to the public path before
 * followup/draft persistence so the sanitizer and MessageThread stay aligned.
 */
export function normalizeInlineAttachmentSrcs(
  html: string,
  ticketId: string | number,
): string {
  return String(html || "").replace(
    /<img\b([^>]*\bdata-attachment-id=["'](\d+)["'][^>]*)\/?>/gi,
    (_full, attrs: string, documentId: string) => {
      const src = attachmentPublicUrl(ticketId, Number(documentId));
      let cleaned = String(attrs).replace(/\ssrc=["'][^"']*["']/i, ` src="${escapeAttr(src)}"`);
      if (!/\ssrc=/i.test(cleaned)) {
        cleaned = ` src="${escapeAttr(src)}"${cleaned}`;
      }
      return `<img${cleaned} />`;
    },
  );
}

export function stripPendingInlineImages(html: string): string {
  return String(html || "").replace(
    new RegExp(`<img\\b[^>]*\\b${PENDING_ATTR}=["'][^"']*["'][^>]*/?>`, "gi"),
    "",
  );
}

function escapeAttr(value: string): string {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
