import { useEffect, useMemo, useRef } from "react";

import { resolveFilePreviewKind } from "../preview/resolveFilePreviewKind";

export type MentionComposerPendingAttachment = {
  id: string;
  fileName: string;
  contentType?: string | null;
  /** When set, kit creates an object URL for image thumbs (revoked on change). */
  file?: File | null;
  /** Explicit preview URL (takes precedence over `file` object URL). */
  previewUrl?: string | null;
  detail?: string;
  busy?: boolean;
};

export function isPendingImageAttachment(
  item: Pick<MentionComposerPendingAttachment, "fileName" | "contentType" | "file">,
): boolean {
  const mime = item.contentType || item.file?.type || null;
  return resolveFilePreviewKind({ fileName: item.fileName, mimeType: mime }) === "image";
}

export function partitionPendingAttachments(
  items: readonly MentionComposerPendingAttachment[],
): {
  images: MentionComposerPendingAttachment[];
  documents: MentionComposerPendingAttachment[];
} {
  const images: MentionComposerPendingAttachment[] = [];
  const documents: MentionComposerPendingAttachment[] = [];
  for (const item of items) {
    if (isPendingImageAttachment(item)) images.push(item);
    else documents.push(item);
  }
  return { images, documents };
}

/**
 * Object URLs for image thumbs derived from `file` when `previewUrl` is absent.
 * Revokes URLs created by this hook on change / unmount.
 */
export function usePendingImageObjectUrls(
  images: readonly MentionComposerPendingAttachment[],
): ReadonlyMap<string, string> {
  const createdRef = useRef<Map<string, string>>(new Map());

  const urls = useMemo(() => {
    const next = new Map<string, string>();
    const created = createdRef.current;
    const keep = new Set<string>();

    for (const item of images) {
      const explicit = item.previewUrl?.trim();
      if (explicit) {
        next.set(item.id, explicit);
        continue;
      }
      const existing = created.get(item.id);
      if (existing) {
        next.set(item.id, existing);
        keep.add(item.id);
        continue;
      }
      if (item.file) {
        const url = URL.createObjectURL(item.file);
        created.set(item.id, url);
        next.set(item.id, url);
        keep.add(item.id);
      }
    }

    for (const [id, url] of Array.from(created.entries())) {
      if (!keep.has(id)) {
        URL.revokeObjectURL(url);
        created.delete(id);
      }
    }

    return next;
  }, [images]);

  useEffect(() => {
    return () => {
      for (const url of createdRef.current.values()) {
        URL.revokeObjectURL(url);
      }
      createdRef.current.clear();
    };
  }, []);

  return urls;
}
