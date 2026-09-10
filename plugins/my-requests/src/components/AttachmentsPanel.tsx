import { FieldLabel } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  attachmentDownloadUrl,
  deleteAttachment,
  downloadAttachmentBlob,
  listAttachments,
  uploadAttachment,
} from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RequestAttachment } from "../types/requests";
import {
  MyRequestsAttachmentPreviewStrip,
  MyRequestsEmptyState,
  MyRequestsFileDropzone,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";

type AttachmentsPanelProps = {
  requestId: string;
  canUpload?: boolean;
  refreshKey?: number;
};

function isImageAttachment(item: RequestAttachment): boolean {
  const ct = (item.content_type || "").toLowerCase();
  if (ct.startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(item.file_name || "");
}

function formatBytes(value: number | null | undefined): string | undefined {
  if (value == null || value <= 0) return undefined;
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function AttachmentsPanel({
  requestId,
  canUpload = false,
  refreshKey = 0,
}: AttachmentsPanelProps) {
  const [items, setItems] = useState<RequestAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [thumbUrls, setThumbUrls] = useState<Record<string, string>>({});
  const thumbUrlsRef = useRef<Record<string, string>>({});

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      const next = await listAttachments(requestId, { signal });
      setItems(next);
    },
    [requestId],
  );

  useEffect(() => {
    const ac = new AbortController();
    reload(ac.signal).catch((err: Error) => {
      if (err.name !== "AbortError") setError(err.message);
    });
    return () => ac.abort();
  }, [reload, refreshKey]);

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
          const blob = await downloadAttachmentBlob(item.id);
          if (cancelled) return;
          next[item.id] = URL.createObjectURL(blob);
        } catch {
          // keep typed icon fallback
        }
      }
      if (cancelled) {
        for (const url of Object.values(next)) URL.revokeObjectURL(url);
        return;
      }
      clearThumbs();
      thumbUrlsRef.current = next;
      setThumbUrls(next);
    })();

    return () => {
      cancelled = true;
      clearThumbs();
    };
  }, [items]);

  const stripItems = useMemo(
    () =>
      items.map((item) => ({
        id: item.id,
        fileName: item.file_name,
        contentType: item.content_type,
        previewUrl: thumbUrls[item.id] || null,
        detail: formatBytes(item.size_bytes),
      })),
    [items, thumbUrls],
  );

  async function onFilesSelected(files: File[]) {
    if (!canUpload || !files.length || busy) return;
    setBusy(true);
    setError(null);
    try {
      for (const file of files) {
        await uploadAttachment(requestId, file, crypto.randomUUID());
      }
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar documento");
    } finally {
      setBusy(false);
    }
  }

  async function onRemove(attachmentId: string) {
    if (!canUpload || busy) return;
    setBusy(true);
    setError(null);
    try {
      await deleteAttachment(attachmentId);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao remover documento");
    } finally {
      setBusy(false);
    }
  }

  return (
    <MyRequestsSectionCard
      title="Documentos da solicitação"
      subtitle="Arquivos que ajudam a entender ou complementar o pedido."
      hint={MY_REQUESTS_HELP_TOOLTIPS.attachments.section}
    >
      <div data-help="attachments">
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
        {canUpload ? (
          <div className="my-requests-upload-field">
            <FieldLabel
              label="Adicionar documento à solicitação"
              hint={MY_REQUESTS_HELP_TOOLTIPS.attachments.upload}
            />
            <MyRequestsFileDropzone
              multiple
              busy={busy}
              disabled={busy}
              accept=".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*"
              onFilesSelected={onFilesSelected}
              ariaLabel="Adicionar documento à solicitação"
            />
          </div>
        ) : null}
        {!error && items.length === 0 ? (
          <MyRequestsEmptyState
            message={
              canUpload
                ? "Nenhum documento ainda. Arraste arquivos ou use a área de envio."
                : "Nenhum documento da solicitação."
            }
          />
        ) : null}
        {items.length > 0 ? (
          <MyRequestsAttachmentPreviewStrip
            mode={canUpload ? "manage" : "preview"}
            items={stripItems}
            onOpen={(item) => {
              window.open(
                attachmentDownloadUrl(item.id),
                "_blank",
                "noopener,noreferrer",
              );
            }}
            onRemove={canUpload ? (item) => void onRemove(item.id) : undefined}
          />
        ) : null}
      </div>
    </MyRequestsSectionCard>
  );
}
