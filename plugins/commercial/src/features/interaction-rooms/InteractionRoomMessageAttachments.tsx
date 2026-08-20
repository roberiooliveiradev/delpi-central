import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { CommercialAttachmentDto } from "../../api/attachmentsApi";
import {
  downloadRoomMessageAttachmentBlob,
  listRoomMessageAttachments,
} from "../../api/interactionRoomsApi";
import { CommercialAttachmentPreviewStrip } from "../../app/commercialUi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import {
  TaskAttachmentPreviewModal,
  type TaskAttachmentPreviewTarget,
} from "../my-day/TaskAttachmentPreviewModal";

type Props = {
  messageId: string;
  /** Bump to reload after local upload or `room.attachment` WS. */
  reloadToken?: number;
  /** Hide attachments already rendered inline in `body_text`. */
  excludeAttachmentIds?: readonly string[];
  /** Notifica thumbs (incl. excluídos) para `resolveAttachmentImageSrc` na thread. */
  onThumbUrlsChange?: (urls: Record<string, string>) => void;
  /** Metadados para lightbox de imagem inline. */
  onItemsChange?: (items: readonly CommercialAttachmentDto[]) => void;
};

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function isImageAttachment(item: CommercialAttachmentDto): boolean {
  const ct = (item.content_type || "").toLowerCase();
  if (ct.startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(item.file_name || "");
}

/**
 * Anexos já enviados na bolha: thumbs (imagem) + chips (docs) + FilePreviewModal.
 */
export function InteractionRoomMessageAttachments({
  messageId,
  reloadToken = 0,
  excludeAttachmentIds = [],
  onThumbUrlsChange,
  onItemsChange,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const id = messageId.trim();
  const [items, setItems] = useState<CommercialAttachmentDto[]>([]);
  const [preview, setPreview] = useState<TaskAttachmentPreviewTarget>(null);
  const [thumbUrls, setThumbUrls] = useState<Record<string, string>>({});
  const thumbUrlsRef = useRef<Record<string, string>>({});
  const excludeSet = useMemo(
    () => new Set(excludeAttachmentIds.map((value) => value.trim()).filter(Boolean)),
    [excludeAttachmentIds],
  );
  const visibleItems = useMemo(
    () => items.filter((item) => !excludeSet.has(item.id)),
    [items, excludeSet],
  );

  const reload = useCallback(async (signal?: AbortSignal) => {
    if (!id) {
      setItems([]);
      return;
    }
    try {
      const next = await listRoomMessageAttachments(id, signal);
      if (signal?.aborted) return;
      setItems(next);
      onItemsChange?.(next);
    } catch {
      if (signal?.aborted) return;
      setItems([]);
      onItemsChange?.([]);
    }
  }, [id, onItemsChange]);

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload, reloadToken]);

  useEffect(() => {
    let cancelled = false;

    const clearThumbs = () => {
      for (const url of Object.values(thumbUrlsRef.current)) {
        URL.revokeObjectURL(url);
      }
      thumbUrlsRef.current = {};
      setThumbUrls({});
    };

    if (items.length === 0) {
      clearThumbs();
      return () => {
        cancelled = true;
      };
    }

    void (async () => {
      const next: Record<string, string> = {};
      for (const item of items) {
        if (!isImageAttachment(item)) continue;
        try {
          const blob = await downloadRoomMessageAttachmentBlob(item.id);
          if (cancelled) return;
          next[item.id] = URL.createObjectURL(blob);
        } catch {
          /* prévia opcional */
        }
      }
      if (cancelled) {
        for (const url of Object.values(next)) URL.revokeObjectURL(url);
        return;
      }
      clearThumbs();
      thumbUrlsRef.current = next;
      setThumbUrls(next);
      onThumbUrlsChange?.(next);
    })();

    return () => {
      cancelled = true;
      clearThumbs();
    };
  }, [items, onThumbUrlsChange]);

  if (visibleItems.length === 0) return null;

  return (
    <div className="cm-room-thread__message-attachments">
      <CommercialAttachmentPreviewStrip
        mode="preview"
        items={visibleItems.map((item) => ({
          id: item.id,
          fileName: item.file_name,
          contentType: item.content_type,
          previewUrl: thumbUrls[item.id] ?? null,
          detail: formatBytes(item.byte_size),
        }))}
        onOpen={(item) => {
          const row = items.find((entry) => entry.id === item.id);
          if (!row) return;
          setPreview({
            kind: "remote",
            id: row.id,
            fileName: row.file_name,
            contentType: row.content_type,
            byteSize: row.byte_size,
          });
        }}
        labels={{
          empty: content.messageAttachmentsEmpty,
          openAriaLabel: (fileName) =>
            content.messageAttachmentOpenAriaLabel.replace("{fileName}", fileName),
          removeAriaLabel: (fileName) =>
            content.messageAttachmentRemoveAriaLabel.replace("{fileName}", fileName),
        }}
      />
      <TaskAttachmentPreviewModal
        open={Boolean(preview)}
        target={preview}
        onClose={() => setPreview(null)}
      />
    </div>
  );
}
