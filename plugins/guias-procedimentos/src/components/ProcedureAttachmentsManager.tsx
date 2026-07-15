import { useCallback, useEffect, useMemo, useState } from "react";

import {
  archiveAttachment,
  listAdminProcedureAttachments,
  triggerAuthenticatedDownload,
  updateAttachmentMetadata,
  uploadProcedureAttachment,
  type ProcedureAttachment,
} from "../api/guiasProcedimentosApi";
import { HttpRequestError } from "../api/httpClient";
import { formatBytes } from "../utils/formatBytes";
import {
  appendHtmlBlock,
  buildAttachmentInsertHtml,
} from "../utils/guideMediaInsert";
import { GuiasConfirmDialog } from "./GuiasConfirmDialog";
import { GuiasFormDialog } from "./GuiasFormDialog";

const ATTACHMENT_MAX = 20 * 1024 * 1024;
const ATTACHMENT_EXT = new Set([
  ".pdf",
  ".doc",
  ".docx",
  ".xls",
  ".xlsx",
  ".txt",
  ".csv",
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
]);

type ProcedureAttachmentsManagerProps = {
  procedureId: string | null;
  contentHtml: string;
  onContentHtmlChange: (next: string) => void;
  disabled?: boolean;
};

type EditState = {
  id: string;
  title: string;
  order_index: number;
} | null;

function extensionOf(name: string): string {
  const idx = name.lastIndexOf(".");
  return idx >= 0 ? name.slice(idx).toLowerCase() : "";
}

export function ProcedureAttachmentsManager({
  procedureId,
  contentHtml,
  onContentHtmlChange,
  disabled = false,
}: ProcedureAttachmentsManagerProps) {
  const [items, setItems] = useState<ProcedureAttachment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [orderIndex, setOrderIndex] = useState(0);
  const [progress, setProgress] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [edit, setEdit] = useState<EditState>(null);
  const [archiveId, setArchiveId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!procedureId) return;
    setLoading(true);
    setError(null);
    try {
      setItems(await listAdminProcedureAttachments(procedureId));
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível carregar os anexos.",
      );
    } finally {
      setLoading(false);
    }
  }, [procedureId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const nextOrder = useMemo(
    () => (items.length ? Math.max(...items.map((a) => a.order_index)) + 1 : 0),
    [items],
  );

  function openUpload() {
    setUploadOpen(true);
    setFile(null);
    setTitle("");
    setOrderIndex(nextOrder);
    setProgress(null);
    setError(null);
  }

  async function submitUpload() {
    if (!procedureId || !file) {
      setError("Selecione um arquivo.");
      return;
    }
    const ext = extensionOf(file.name);
    if (ext && !ATTACHMENT_EXT.has(ext)) {
      setError(
        "Tipo não permitido. Use PDF, DOC(X), XLS(X), TXT, CSV ou imagem (JPEG/PNG/WebP).",
      );
      return;
    }
    if (file.size > ATTACHMENT_MAX) {
      setError("Anexo excede o limite de 20 MB.");
      return;
    }
    setBusy(true);
    setError(null);
    setFeedback(null);
    setProgress(0);
    try {
      await uploadProcedureAttachment(
        procedureId,
        file,
        {
          title: title.trim() || file.name,
          order_index: Number(orderIndex) || 0,
        },
        (ratio) => setProgress(ratio),
      );
      setFeedback("Anexo enviado.");
      setUploadOpen(false);
      setFile(null);
      await reload();
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível enviar o anexo.",
      );
    } finally {
      setBusy(false);
      setProgress(null);
    }
  }

  async function submitEdit() {
    if (!edit) return;
    setBusy(true);
    setError(null);
    try {
      await updateAttachmentMetadata(edit.id, {
        title: edit.title.trim(),
        order_index: Number(edit.order_index) || 0,
      });
      setFeedback("Metadados atualizados.");
      setEdit(null);
      await reload();
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível atualizar.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function confirmArchive() {
    if (!archiveId) return;
    setBusy(true);
    setError(null);
    try {
      await archiveAttachment(archiveId);
      setFeedback("Anexo arquivado.");
      setArchiveId(null);
      await reload();
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível arquivar.",
      );
      setArchiveId(null);
    } finally {
      setBusy(false);
    }
  }

  function insertAttachment(item: ProcedureAttachment) {
    const block = buildAttachmentInsertHtml(item);
    onContentHtmlChange(appendHtmlBlock(contentHtml, block));
    setFeedback("Referência do anexo inserida no artigo.");
  }

  async function copyRef(item: ProcedureAttachment) {
    try {
      await navigator.clipboard.writeText(buildAttachmentInsertHtml(item));
      setFeedback("HTML copiado.");
    } catch {
      setFeedback("Não foi possível copiar. Use «Inserir no artigo».");
    }
  }

  async function download(item: ProcedureAttachment) {
    try {
      await triggerAuthenticatedDownload(
        item.download_url,
        item.original_filename || item.title || "anexo",
      );
    } catch (err: unknown) {
      setError(
        err instanceof HttpRequestError
          ? err.message
          : "Não foi possível baixar o anexo.",
      );
    }
  }

  if (!procedureId) {
    return (
      <div className="gp-asset-panel">
        <p className="gp-intro">
          Salve o rascunho do procedimento antes de enviar anexos.
        </p>
      </div>
    );
  }

  return (
    <div className="gp-asset-panel">
      <div className="gp-asset-panel__toolbar">
        <button
          type="button"
          className="gp-btn gp-btn--secondary gp-btn--compact"
          disabled={disabled || busy}
          onClick={openUpload}
        >
          Enviar anexo
        </button>
      </div>
      <p className="gp-field__hint">
        Até 20 MB — PDF, DOC(X), XLS(X), TXT, CSV ou imagem (JPEG/PNG/WebP).
        Pré-visualização de Office não é oferecida neste navegador.
      </p>

      {feedback ? (
        <p className="gp-feedback gp-feedback--ok">{feedback}</p>
      ) : null}
      {error ? <p className="gp-feedback gp-feedback--error">{error}</p> : null}
      {loading ? <p className="gp-intro">Carregando anexos…</p> : null}

      {!loading && items.length === 0 ? (
        <p className="gp-intro">Nenhum anexo cadastrado.</p>
      ) : null}

      {items.length > 0 ? (
        <div className="gp-admin-table-wrap">
          <table className="gp-admin-table">
            <thead>
              <tr>
                <th scope="col">Título</th>
                <th scope="col">Arquivo</th>
                <th scope="col">Tipo</th>
                <th scope="col">Tamanho</th>
                <th scope="col">Ordem</th>
                <th scope="col">Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.title || "Sem título"}</td>
                  <td>{item.original_filename || "—"}</td>
                  <td>{item.mime_type || extensionOf(item.original_filename || "") || "—"}</td>
                  <td>{formatBytes(item.size_bytes)}</td>
                  <td>{item.order_index}</td>
                  <td>
                    <div className="gp-admin-row-actions">
                      <button
                        type="button"
                        className="gp-btn gp-btn--ghost gp-btn--compact"
                        onClick={() => void download(item)}
                      >
                        Baixar
                      </button>
                      <button
                        type="button"
                        className="gp-btn gp-btn--ghost gp-btn--compact"
                        disabled={disabled}
                        onClick={() =>
                          setEdit({
                            id: item.id,
                            title: item.title,
                            order_index: item.order_index,
                          })
                        }
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="gp-btn gp-btn--secondary gp-btn--compact"
                        disabled={disabled}
                        onClick={() => insertAttachment(item)}
                      >
                        Inserir no artigo
                      </button>
                      <button
                        type="button"
                        className="gp-btn gp-btn--ghost gp-btn--compact"
                        onClick={() => void copyRef(item)}
                      >
                        Copiar HTML
                      </button>
                      <button
                        type="button"
                        className="gp-btn gp-btn--ghost gp-btn--compact"
                        disabled={disabled || busy}
                        onClick={() => setArchiveId(item.id)}
                      >
                        Arquivar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <GuiasFormDialog
        open={uploadOpen}
        title="Enviar anexo"
        busy={busy}
        confirmLabel="Enviar"
        confirmDisabled={!file}
        onCancel={() => !busy && setUploadOpen(false)}
        onConfirm={() => void submitUpload()}
      >
        <label className="gp-field">
          <span>Arquivo</span>
          <input
            className="gp-input"
            type="file"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.jpg,.jpeg,.png,.webp,application/pdf,text/plain,text/csv"
            disabled={busy}
            onChange={(event) => {
              const next = event.target.files?.[0] ?? null;
              setFile(next);
              if (next && !title.trim()) setTitle(next.name);
            }}
          />
          {file ? (
            <span className="gp-field__hint">
              {file.name} · {formatBytes(file.size)}
            </span>
          ) : null}
        </label>
        <label className="gp-field">
          <span>Título</span>
          <input
            className="gp-input"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            disabled={busy}
          />
        </label>
        <label className="gp-field">
          <span>Ordem</span>
          <input
            className="gp-input"
            type="number"
            min={0}
            value={orderIndex}
            onChange={(event) => setOrderIndex(Number(event.target.value))}
            disabled={busy}
          />
        </label>
        {progress != null ? (
          <p className="gp-field__hint">Envio: {Math.round(progress * 100)}%</p>
        ) : null}
      </GuiasFormDialog>

      <GuiasFormDialog
        open={edit != null}
        title="Editar metadados do anexo"
        busy={busy}
        onCancel={() => !busy && setEdit(null)}
        onConfirm={() => void submitEdit()}
      >
        {edit ? (
          <>
            <p className="gp-field__hint">
              Para substituir o arquivo, envie um novo e arquive o anterior.
            </p>
            <label className="gp-field">
              <span>Título</span>
              <input
                className="gp-input"
                value={edit.title}
                onChange={(event) =>
                  setEdit({ ...edit, title: event.target.value })
                }
                disabled={busy}
              />
            </label>
            <label className="gp-field">
              <span>Ordem</span>
              <input
                className="gp-input"
                type="number"
                min={0}
                value={edit.order_index}
                onChange={(event) =>
                  setEdit({
                    ...edit,
                    order_index: Number(event.target.value),
                  })
                }
                disabled={busy}
              />
            </label>
          </>
        ) : null}
      </GuiasFormDialog>

      <GuiasConfirmDialog
        open={archiveId != null}
        title="Arquivar anexo"
        message="O anexo deixará de aparecer publicamente e nas listagens ativas. O arquivo permanece no armazenamento (sem exclusão física)."
        confirmLabel="Arquivar"
        busy={busy}
        variant="danger"
        onCancel={() => !busy && setArchiveId(null)}
        onConfirm={() => void confirmArchive()}
      />
    </div>
  );
}
