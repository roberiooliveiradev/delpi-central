import { useCallback, useEffect, useRef, useState } from "react";

import {
  deleteAttachment,
  downloadAttachmentBlob,
  listTaskAttachments,
  uploadTaskAttachment,
  type CommercialAttachmentDto,
} from "../../api/attachmentsApi";
import {
  CommercialAttachmentFileList,
  CommercialAttachmentPreviewStrip,
  CommercialFileDropzone,
} from "../../app/commercialUi";
import {
  TaskAttachmentPreviewModal,
  type TaskAttachmentPreviewTarget,
} from "./TaskAttachmentPreviewModal";

export type TaskAttachmentsMode = "preview" | "manage";

type TaskAttachmentsBlockProps = {
  taskId: string;
  initialCount?: number;
  /** preview = só visualizar; manage = adicionar/remover (fluxo Editar / Nova). */
  mode: TaskAttachmentsMode;
  /** Sem SectionCard — corpo do DetailCard da tarefa. */
  embedded?: boolean;
  onChanged?: () => void;
  notifyError: (message: string) => void;
  notifySuccess: (message: string) => void;
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

const ATTACH_ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain";

export function TaskAttachmentsBlock({
  taskId,
  initialCount = 0,
  mode,
  embedded = false,
  onChanged,
  notifyError,
  notifySuccess,
}: TaskAttachmentsBlockProps) {
  const canManage = mode === "manage";
  const [items, setItems] = useState<CommercialAttachmentDto[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [preview, setPreview] = useState<TaskAttachmentPreviewTarget>(null);
  const [loadedOnce, setLoadedOnce] = useState(false);
  const [thumbUrls, setThumbUrls] = useState<Record<string, string>>({});
  const thumbUrlsRef = useRef<Record<string, string>>({});

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const next = await listTaskAttachments(taskId);
      setItems(next);
      setLoadedOnce(true);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao listar anexos.");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [notifyError, taskId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    let cancelled = false;

    const clearThumbs = () => {
      for (const url of Object.values(thumbUrlsRef.current)) {
        URL.revokeObjectURL(url);
      }
      thumbUrlsRef.current = {};
      setThumbUrls({});
    };

    if (mode !== "preview" || items.length === 0) {
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
          /* prévia opcional — ícone permanece */
        }
      }
      if (cancelled) {
        for (const url of Object.values(next)) URL.revokeObjectURL(url);
        return;
      }
      for (const url of Object.values(thumbUrlsRef.current)) {
        URL.revokeObjectURL(url);
      }
      thumbUrlsRef.current = next;
      setThumbUrls(next);
    })();

    return () => {
      cancelled = true;
      for (const url of Object.values(thumbUrlsRef.current)) {
        URL.revokeObjectURL(url);
      }
      thumbUrlsRef.current = {};
    };
  }, [items, mode]);

  const onUpload = async (files: File[]) => {
    const file = files[0];
    if (!file || !canManage) return;
    setBusyId("upload");
    try {
      await uploadTaskAttachment(taskId, file);
      notifySuccess("Anexo enviado.");
      await reload();
      onChanged?.();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao enviar anexo.");
    } finally {
      setBusyId(null);
    }
  };

  const onDownload = async (item: { id: string; fileName: string }) => {
    setBusyId(item.id);
    try {
      const blob = await downloadAttachmentBlob(item.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = item.fileName;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao baixar anexo.");
    } finally {
      setBusyId(null);
    }
  };

  const onDelete = async (item: { id: string }) => {
    if (!canManage) return;
    setBusyId(item.id);
    try {
      await deleteAttachment(item.id);
      notifySuccess("Anexo removido.");
      await reload();
      onChanged?.();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao remover anexo.");
    } finally {
      setBusyId(null);
    }
  };

  const onOpen = (item: { id: string; fileName: string }) => {
    const full = items.find((row) => row.id === item.id);
    setPreview({
      kind: "remote",
      id: item.id,
      fileName: item.fileName,
      contentType: full?.content_type,
      byteSize: full?.byte_size,
    });
  };

  const count = loadedOnce ? items.length : initialCount;
  const heading =
    mode === "preview"
      ? count > 0
        ? `Anexos (${count})`
        : "Anexos"
      : count > 0
        ? `Arquivos anexados (${count})`
        : "Arquivos anexados";

  return (
    <>
      <div className={embedded ? "cm-my-day-attachments cm-my-day-attachments--embedded" : "cm-my-day-attachments"}>
        {mode === "preview" ? (
          <>
            {loading && !loadedOnce ? <p className="cm-hint-text">Carregando anexos…</p> : null}
            {loadedOnce || !loading ? (
              <CommercialAttachmentPreviewStrip
                heading={heading}
                items={items.map((item) => ({
                  id: item.id,
                  fileName: item.file_name,
                  contentType: item.content_type,
                  detail: formatBytes(item.byte_size),
                  previewUrl: thumbUrls[item.id] ?? null,
                }))}
                emptyMessage="Nenhum anexo nesta tarefa."
                onOpen={(item) => onOpen({ id: item.id, fileName: item.fileName })}
              />
            ) : null}
          </>
        ) : (
          <>
            <h3 className="cm-my-day-attachments__title">{heading}</h3>
            <CommercialFileDropzone
              multiple={false}
              accept={ATTACH_ACCEPT}
              busy={busyId === "upload"}
              disabled={busyId === "upload"}
              onFilesSelected={(files) => void onUpload(files)}
              labels={{
                title: busyId === "upload" ? "Enviando…" : "Arraste ou clique para anexar",
                hint: "PDF, imagem, TXT, Word ou Excel · máx. 10 MB",
              }}
            />
            {loading && !loadedOnce ? <p className="cm-hint-text">Carregando anexos…</p> : null}
            {loadedOnce || !loading ? (
              <CommercialAttachmentFileList
                items={items.map((item) => ({
                  id: item.id,
                  fileName: item.file_name,
                  detail: formatBytes(item.byte_size),
                  busy: busyId === item.id,
                }))}
                emptyMessage="Nenhum arquivo anexado nesta tarefa."
                onOpen={onOpen}
                onDownload={(item) => void onDownload(item)}
                onRemove={(item) => void onDelete(item)}
                canRemove
              />
            ) : null}
          </>
        )}
      </div>
      <TaskAttachmentPreviewModal
        target={preview}
        open={Boolean(preview)}
        onClose={() => setPreview(null)}
      />
    </>
  );
}
