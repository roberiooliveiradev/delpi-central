import { useCallback, useEffect, useState } from "react";

import {
  deleteAttachment,
  downloadAttachmentBlob,
  listTaskAttachments,
  uploadTaskAttachment,
  type CommercialAttachmentDto,
} from "../../api/attachmentsApi";
import {
  CommercialAttachmentFileList,
  CommercialFileDropzone,
} from "../../app/commercialUi";
import {
  TaskAttachmentPreviewModal,
  type TaskAttachmentPreviewTarget,
} from "./TaskAttachmentPreviewModal";

type TaskAttachmentsBlockProps = {
  taskId: string;
  initialCount?: number;
  canManage: boolean;
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

const ATTACH_ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain";

export function TaskAttachmentsBlock({
  taskId,
  initialCount = 0,
  canManage,
  embedded = false,
  onChanged,
  notifyError,
  notifySuccess,
}: TaskAttachmentsBlockProps) {
  const [items, setItems] = useState<CommercialAttachmentDto[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [preview, setPreview] = useState<TaskAttachmentPreviewTarget>(null);
  const [loadedOnce, setLoadedOnce] = useState(false);

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
  const heading = count > 0 ? `Arquivos anexados (${count})` : "Arquivos anexados";

  return (
    <>
      <div className={embedded ? "cm-my-day-attachments" : "cm-my-day-attachments"}>
        <h3 className="cm-my-day-attachments__title">{heading}</h3>
        {canManage ? (
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
        ) : null}
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
            onRemove={canManage ? (item) => void onDelete(item) : undefined}
            canRemove={canManage}
          />
        ) : null}
      </div>
      <TaskAttachmentPreviewModal
        target={preview}
        open={Boolean(preview)}
        onClose={() => setPreview(null)}
      />
    </>
  );
}
