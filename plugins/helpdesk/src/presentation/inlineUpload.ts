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

/**
 * Reply draft persists BFF paths (stable). `<img src>` without Bearer → 401.
 * Reload must fetch blobs and rewrite src for the composer preview.
 */
export async function hydrateInlineAttachmentSrcs(
  html: string,
  ticketId: string | number,
  fetchBlob: (ticketId: string, documentId: number) => Promise<Blob>,
): Promise<{ html: string; objectUrls: string[] }> {
  const source = String(html || "");
  const ids = listDocumentIdsInHtml(source);
  if (ids.length === 0) {
    return { html: source, objectUrls: [] };
  }
  const objectUrls: string[] = [];
  const byId = new Map<number, string>();
  await Promise.all(
    ids.map(async (documentId) => {
      try {
        const blob = await fetchBlob(String(ticketId), documentId);
        const url = URL.createObjectURL(blob);
        objectUrls.push(url);
        byId.set(documentId, url);
      } catch {
        // Leave the public path; caller may show a soft warning.
      }
    }),
  );
  if (byId.size === 0) {
    return { html: source, objectUrls };
  }
  let next = source;
  for (const [documentId, blobUrl] of byId) {
    const publicSrc = attachmentPublicUrl(ticketId, documentId);
    const publicRe = new RegExp(
      `(<img\\b[^>]*\\bsrc=["'])${escapeRegExp(publicSrc)}(["'][^>]*>)`,
      "gi",
    );
    next = next.replace(publicRe, `$1${blobUrl}$2`);
    const idRe = new RegExp(
      `<img\\b([^>]*\\bdata-attachment-id=["']${documentId}["'][^>]*)\\/?>`,
      "gi",
    );
    next = next.replace(idRe, (_full, attrs: string) => {
      let cleaned = String(attrs).replace(/\ssrc=["'][^"']*["']/i, ` src="${escapeAttr(blobUrl)}"`);
      if (!/\ssrc=/i.test(cleaned)) {
        cleaned = ` src="${escapeAttr(blobUrl)}"${cleaned}`;
      }
      return `<img${cleaned} />`;
    });
  }
  return { html: next, objectUrls };
}

function listDocumentIdsInHtml(html: string): number[] {
  const ids: number[] = [];
  const seen = new Set<number>();
  const fromPath = /\/apps\/helpdesk-api\/tickets\/\d+\/attachments\/(\d+)/gi;
  const fromAttr = /data-attachment-id=["'](\d+)["']/gi;
  let match: RegExpExecArray | null;
  while ((match = fromPath.exec(html))) {
    const id = Number(match[1]);
    if (!Number.isFinite(id) || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  while ((match = fromAttr.exec(html))) {
    const id = Number(match[1]);
    if (!Number.isFinite(id) || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
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
