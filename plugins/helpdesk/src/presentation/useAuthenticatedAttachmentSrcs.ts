/**
 * Canonical helpdesk flow for authenticated attachment images in composers:
 *
 *   persist HTML  →  BFF public path + data-attachment-id
 *   display       →  blob: via resolveAttachmentImageSrc (Bearer fetch)
 *
 * Same contract as MessageThread / MentionComposer — never store blob: in draft state.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { attachmentPublicUrl, listPendingInlineIds } from "./inlineUpload";
import { listHelpdeskAttachmentIdsInHtml, stampHelpdeskAttachmentIds } from "./ticketView";

export type FetchTicketAttachmentBlob = (
  ticketId: string,
  documentId: number,
) => Promise<Blob>;

/**
 * Stable HTML for draft/API:
 *   data-attachment-id → BFF public path (when ticketId known)
 *   data-attachment-pending → attachment:pending:{id} (never blob:/data:)
 */
export function persistHelpdeskAttachmentHtml(
  html: string,
  ticketId?: string | number | null,
): string {
  let next = stampHelpdeskAttachmentIds(html || "");
  const ticket = ticketId != null ? String(ticketId).trim() : "";
  if (ticket) {
    next = next.replace(
      /<img\b([^>]*\bdata-attachment-id=["'](\d+)["'][^>]*)\/?>/gi,
      (_full, attrs: string, documentId: string) => {
        const src = attachmentPublicUrl(ticket, Number(documentId));
        let cleaned = String(attrs).replace(/\ssrc=["'][^"']*["']/i, ` src="${src}"`);
        if (!/\ssrc=/i.test(cleaned)) cleaned = ` src="${src}"${cleaned}`;
        return `<img${cleaned} />`;
      },
    );
  }
  return next.replace(
    /<img\b([^>]*\bdata-attachment-pending=["']([^"']+)["'][^>]*)\/?>/gi,
    (_full, attrs: string, pendingId: string) => {
      const token = `attachment:pending:${pendingId}`;
      let cleaned = String(attrs).replace(/\ssrc=["'][^"']*["']/i, ` src="${token}"`);
      if (!/\ssrc=/i.test(cleaned)) cleaned = ` src="${token}"${cleaned}`;
      return `<img${cleaned} />`;
    },
  );
}

/** Resolve display blob: direct id, or pending→document alias after upload rewrite. */
export function resolveAttachmentDisplaySrc(
  attachmentId: string,
  srcs: Record<string, string>,
  pendingToDocument: Record<string, string>,
): string | null {
  const id = String(attachmentId || "").trim();
  if (!id) return null;
  if (srcs[id]) return srcs[id];
  const documentId = pendingToDocument[id];
  if (documentId && srcs[documentId]) return srcs[documentId];
  return null;
}

/**
 * Move seed blob from pending key → document id without revoking the object URL.
 * Keeps a pending→document alias so a focused editor still resolving
 * `data-attachment-pending` keeps showing the image after upload rewrite.
 */
export function transferPendingSrcMaps(
  srcs: Record<string, string>,
  pendingToDocument: Record<string, string>,
  pendingId: string,
  documentId: string | number,
): { srcs: Record<string, string>; pendingToDocument: Record<string, string>; url: string | null } {
  const pendingKey = String(pendingId || "").trim();
  const docKey = String(documentId);
  if (!pendingKey || !docKey) {
    return { srcs, pendingToDocument, url: null };
  }
  const url = srcs[pendingKey] || null;
  const nextSrcs = { ...srcs };
  const nextAlias = { ...pendingToDocument, [pendingKey]: docKey };
  if (url) {
    nextSrcs[docKey] = url;
    delete nextSrcs[pendingKey];
  }
  return { srcs: nextSrcs, pendingToDocument: nextAlias, url };
}

/** Prune srcs to needed keys; only revoke blob URLs that no remaining key references. */
export function pruneAttachmentSrcs(
  current: Record<string, string>,
  needed: ReadonlySet<string>,
  revoke: (url: string) => void,
): Record<string, string> {
  const next: Record<string, string> = {};
  for (const [id, url] of Object.entries(current)) {
    if (needed.has(id)) next[id] = url;
  }
  const retained = new Set(Object.values(next));
  for (const [id, url] of Object.entries(current)) {
    if (!needed.has(id) && !retained.has(url)) revoke(url);
  }
  return next;
}

export function useAuthenticatedAttachmentSrcs(args: {
  ticketId: string;
  html: string;
  fetchBlob: FetchTicketAttachmentBlob;
  /** Extra ids (e.g. ticket.attachments) to warm the cache. */
  extraDocumentIds?: readonly number[];
}): {
  persistHtml: (html: string) => string;
  resolveAttachmentImageSrc: (attachmentId: string) => string | null;
  persistAttachmentImageSrc: (attachmentId: string) => string | null;
  seedBlobUrl: (documentId: number | string, blobUrl: string) => void;
  seedFile: (documentId: number | string, file: File) => string;
  /** After upload: keep preview while DOM still has data-attachment-pending. */
  transferPendingSeed: (pendingId: string, documentId: number | string) => string | null;
} {
  const { ticketId, html, fetchBlob, extraDocumentIds } = args;
  const [srcs, setSrcs] = useState<Record<string, string>>({});
  const srcsRef = useRef(srcs);
  srcsRef.current = srcs;
  const ownedUrlsRef = useRef<Set<string>>(new Set());
  const pendingToDocumentRef = useRef<Record<string, string>>({});

  const attachmentKeys = useMemo(() => {
    const stamped = stampHelpdeskAttachmentIds(html || "");
    const keys = new Set<string>();
    for (const id of listHelpdeskAttachmentIdsInHtml(stamped)) {
      keys.add(String(id));
    }
    for (const pendingId of listPendingInlineIds(stamped)) {
      keys.add(pendingId);
    }
    for (const id of extraDocumentIds || []) {
      if (Number.isFinite(id) && id > 0) keys.add(String(id));
    }
    // Keep document ids that pending aliases still point at (focused DOM may lag HTML).
    for (const docId of Object.values(pendingToDocumentRef.current)) {
      if (docId) keys.add(docId);
    }
    return [...keys].sort();
  }, [html, extraDocumentIds]);

  const documentIds = useMemo(
    () =>
      attachmentKeys
        .map((key) => Number(key))
        .filter((id) => Number.isFinite(id) && id > 0)
        .sort((a, b) => a - b),
    [attachmentKeys],
  );

  const revokeOwned = useCallback((url: string) => {
    if (!ownedUrlsRef.current.has(url)) return;
    ownedUrlsRef.current.delete(url);
    try {
      URL.revokeObjectURL(url);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const needed = new Set(attachmentKeys);

    setSrcs((current) => pruneAttachmentSrcs(current, needed, revokeOwned));

    void Promise.all(
      documentIds.map(async (documentId) => {
        const key = String(documentId);
        if (srcsRef.current[key]) return;
        try {
          const blob = await fetchBlob(ticketId, documentId);
          if (cancelled) return;
          const url = URL.createObjectURL(blob);
          ownedUrlsRef.current.add(url);
          setSrcs((current) => {
            if (current[key]) {
              revokeOwned(url);
              return current;
            }
            return { ...current, [key]: url };
          });
        } catch {
          /* soft-fail: preview stays broken until retry */
        }
      }),
    );

    return () => {
      cancelled = true;
    };
  }, [attachmentKeys, documentIds, ticketId, fetchBlob, revokeOwned]);

  useEffect(() => {
    return () => {
      for (const url of ownedUrlsRef.current) {
        try {
          URL.revokeObjectURL(url);
        } catch {
          /* ignore */
        }
      }
      ownedUrlsRef.current.clear();
      pendingToDocumentRef.current = {};
    };
  }, []);

  const persistHtml = useCallback(
    (raw: string) => persistHelpdeskAttachmentHtml(raw, ticketId),
    [ticketId],
  );

  const resolveAttachmentImageSrc = useCallback(
    (attachmentId: string) =>
      resolveAttachmentDisplaySrc(attachmentId, srcs, pendingToDocumentRef.current),
    [srcs],
  );

  const persistAttachmentImageSrc = useCallback(
    (attachmentId: string) => {
      const id = Number(attachmentId);
      if (Number.isFinite(id) && id > 0) {
        return attachmentPublicUrl(ticketId, id);
      }
      const pending = String(attachmentId || "").trim();
      if (!pending) return null;
      // Pending uuid — stable token so draft/F5 never keeps blob:
      return `attachment:pending:${pending}`;
    },
    [ticketId],
  );

  const seedBlobUrl = useCallback(
    (documentId: number | string, blobUrl: string) => {
      const key = String(documentId);
      setSrcs((current) => {
        const previous = current[key];
        if (previous && previous !== blobUrl) revokeOwned(previous);
        ownedUrlsRef.current.add(blobUrl);
        const next = { ...current, [key]: blobUrl };
        srcsRef.current = next;
        return next;
      });
    },
    [revokeOwned],
  );

  const seedFile = useCallback(
    (documentId: number | string, file: File) => {
      const url = URL.createObjectURL(file);
      seedBlobUrl(documentId, url);
      return url;
    },
    [seedBlobUrl],
  );

  const transferPendingSeed = useCallback((pendingId: string, documentId: number | string) => {
    const transferred = transferPendingSrcMaps(
      srcsRef.current,
      pendingToDocumentRef.current,
      pendingId,
      documentId,
    );
    pendingToDocumentRef.current = transferred.pendingToDocument;
    srcsRef.current = transferred.srcs;
    setSrcs(transferred.srcs);
    return transferred.url;
  }, []);

  return {
    persistHtml,
    resolveAttachmentImageSrc,
    persistAttachmentImageSrc,
    seedBlobUrl,
    seedFile,
    transferPendingSeed,
  };
}
