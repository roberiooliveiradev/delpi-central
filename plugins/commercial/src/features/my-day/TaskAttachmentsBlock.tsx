import { useCallback, useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import {
  deleteAttachment,
  downloadAttachmentBlob,
  listTaskAttachments,
  uploadTaskAttachment,
  type CommercialAttachmentDto,
} from "../../api/attachmentsApi";

type TaskAttachmentsBlockProps = {
  taskId: string;
  initialCount?: number;
  canManage: boolean;
  onChanged?: () => void;
  notifyError: (message: string) => void;
  notifySuccess: (message: string) => void;
};

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function TaskAttachmentsBlock({
  taskId,
  initialCount = 0,
  canManage,
  onChanged,
  notifyError,
  notifySuccess,
}: TaskAttachmentsBlockProps) {
  const [open, setOpen] = useState(initialCount > 0);
  const [items, setItems] = useState<CommercialAttachmentDto[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const next = await listTaskAttachments(taskId);
      setItems(next);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao listar anexos.");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [notifyError, taskId]);

  useEffect(() => {
    if (!open) return;
    void reload();
  }, [open, reload]);

  const onUpload = async (fileList: FileList | null) => {
    const file = fileList?.[0];
    if (!file || !canManage) return;
    setBusyId("upload");
    try {
      await uploadTaskAttachment(taskId, file);
      notifySuccess("Anexo enviado.");
      setOpen(true);
      await reload();
      onChanged?.();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao enviar anexo.");
    } finally {
      setBusyId(null);
    }
  };

  const onDownload = async (item: CommercialAttachmentDto) => {
    setBusyId(item.id);
    try {
      const blob = await downloadAttachmentBlob(item.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = item.file_name;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao baixar anexo.");
    } finally {
      setBusyId(null);
    }
  };

  const onDelete = async (item: CommercialAttachmentDto) => {
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

  const countLabel = open ? items.length : initialCount;

  return (
    <div className="cm-task-attachments">
      <div className="cm-task-attachments__toolbar">
        <ActionButton variant="ghost" onClick={() => setOpen((value) => !value)}>
          {open ? "Ocultar anexos" : `Anexos${countLabel > 0 ? ` (${countLabel})` : ""}`}
        </ActionButton>
        {canManage ? (
          <label className="cm-task-attachments__upload">
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain"
              disabled={busyId === "upload"}
              onChange={(event) => {
                void onUpload(event.target.files);
                event.target.value = "";
              }}
            />
            <span>{busyId === "upload" ? "Enviando…" : "Anexar arquivo"}</span>
          </label>
        ) : null}
      </div>
      {open ? (
        <div className="cm-task-attachments__body" aria-live="polite">
          {loading ? <p className="cm-hint-text">Carregando anexos…</p> : null}
          {!loading && items.length === 0 ? (
            <p className="cm-hint-text">Nenhum anexo nesta tarefa.</p>
          ) : null}
          {!loading && items.length > 0 ? (
            <ul className="cm-task-attachments__list">
              {items.map((item) => (
                <li key={item.id}>
                  <div className="cm-task-attachments__meta">
                    <strong>{item.file_name}</strong>
                    <span>{formatBytes(item.byte_size)}</span>
                  </div>
                  <div className="cm-row-actions">
                    <ActionButton
                      variant="ghost"
                      disabled={busyId === item.id}
                      onClick={() => void onDownload(item)}
                    >
                      Baixar
                    </ActionButton>
                    {canManage ? (
                      <ActionButton
                        variant="ghost"
                        disabled={busyId === item.id}
                        onClick={() => void onDelete(item)}
                      >
                        Remover
                      </ActionButton>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
