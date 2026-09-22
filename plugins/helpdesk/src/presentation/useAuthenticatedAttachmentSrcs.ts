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
} {
  const { ticketId, html, fetchBlob, extraDocumentIds } = args;
  const [srcs, setSrcs] = useState<Record<string, string>>({});
  const srcsRef = useRef(srcs);
  srcsRef.current = srcs;
  const ownedUrlsRef = useRef<Set<string>>(new Set());

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

    setSrcs((current) => {
      const next: Record<string, string> = {};
      for (const [id, url] of Object.entries(current)) {
        if (needed.has(id)) {
          next[id] = url;
        } else {
          revokeOwned(url);
        }
      }
      return next;
    });

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
    };
  }, []);

  const persistHtml = useCallback(
    (raw: string) => persistHelpdeskAttachmentHtml(raw, ticketId),
    [ticketId],
  );

  const resolveAttachmentImageSrc = useCallback(
    (attachmentId: string) => srcs[attachmentId] || null,
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
        return { ...current, [key]: blobUrl };
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

  return {
    persistHtml,
    resolveAttachmentImageSrc,
    persistAttachmentImageSrc,
    seedBlobUrl,
    seedFile,
  };
}
