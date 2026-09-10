import { ActionButton, FieldLabel } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
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
  MyRequestsFormActions,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";
import {
  revokeStagedPreviews,
  stageFiles,
  type StagedAttachment,
} from "./StagedAttachmentsField";
import {
  RequestFilePreviewModal,
  type RequestFilePreviewTarget,
} from "./RequestFilePreviewModal";

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
  const [pending, setPending] = useState<StagedAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [thumbUrls, setThumbUrls] = useState<Record<string, string>>({});
  const thumbUrlsRef = useRef<Record<string, string>>({});
  const [preview, setPreview] = useState<RequestFilePreviewTarget>(null);

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
    return () => revokeStagedPreviews(pending);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- revoke on unmount
  }, []);

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
          // typed icon fallback
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

  const savedStripItems = useMemo(
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

  const pendingStripItems = useMemo(
    () =>
      pending.map((item) => ({
        id: item.id,
        fileName: item.file.name,
        contentType: item.file.type || null,
        previewUrl: item.previewUrl,
        detail: formatBytes(item.file.size),
      })),
    [pending],
  );

  function onFilesSelected(files: File[]) {
    if (!canUpload || !files.length || busy) return;
    setError(null);
    setPending((prev) => [...prev, ...stageFiles(files)]);
  }

  function onRemovePending(id: string) {
    setPending((prev) => {
      const removed = prev.find((row) => row.id === id);
      if (removed?.previewUrl) URL.revokeObjectURL(removed.previewUrl);
      return prev.filter((row) => row.id !== id);
    });
  }

  async function onSavePending() {
    if (!canUpload || !pending.length || busy) return;
    setBusy(true);
    setError(null);
    const queue = [...pending];
    try {
      for (const staged of queue) {
        await uploadAttachment(requestId, staged.file, crypto.randomUUID());
      }
      revokeStagedPreviews(queue);
      setPending([]);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar documento");
    } finally {
      setBusy(false);
    }
  }

  async function onRemoveSaved(attachmentId: string) {
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

  const empty =
    !error && items.length === 0 && pending.length === 0;

  return (
    <>
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

          {pending.length > 0 ? (
            <div className="my-requests-upload-field">
              <FieldLabel
                label="Pendentes de envio"
                hint={MY_REQUESTS_HELP_TOOLTIPS.attachments.pending}
              />
              <MyRequestsAttachmentPreviewStrip
                mode="manage"
                items={pendingStripItems}
                emptyMessage="Nenhum arquivo pendente."
                onOpen={(item) => {
                  const staged = pending.find((row) => row.id === item.id);
                  if (!staged) return;
                  setPreview({ kind: "local", file: staged.file });
                }}
                onRemove={(item) => onRemovePending(item.id)}
              />
              <MyRequestsFormActions>
                <ActionButton
                  type="button"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => {
                    revokeStagedPreviews(pending);
                    setPending([]);
                  }}
                >
                  Descartar
                </ActionButton>
                <ActionButton
                  type="button"
                  variant="primary"
                  disabled={busy}
                  onClick={() => void onSavePending()}
                >
                  {busy ? "Salvando…" : "Salvar documentos"}
                </ActionButton>
              </MyRequestsFormActions>
            </div>
          ) : null}

          {empty ? (
            <MyRequestsEmptyState
              message={
                canUpload
                  ? "Nenhum documento ainda. Selecione arquivos e use Salvar documentos."
                  : "Nenhum documento da solicitação."
              }
            />
          ) : null}

          {items.length > 0 ? (
            <MyRequestsAttachmentPreviewStrip
              mode={canUpload ? "manage" : "preview"}
              heading={canUpload ? "Documentos salvos" : undefined}
              items={savedStripItems}
              onOpen={(item) => {
                const saved = items.find((row) => row.id === item.id);
                if (!saved) return;
                setPreview({
                  kind: "attachment",
                  id: saved.id,
                  fileName: saved.file_name,
                  contentType: saved.content_type,
                  byteSize: saved.size_bytes,
                });
              }}
              onRemove={
                canUpload ? (item) => void onRemoveSaved(item.id) : undefined
              }
            />
          ) : null}
        </div>
      </MyRequestsSectionCard>

      <RequestFilePreviewModal
        target={preview}
        open={Boolean(preview)}
        onClose={() => setPreview(null)}
      />
    </>
  );
}
