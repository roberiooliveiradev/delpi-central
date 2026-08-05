import { type FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { Archive, Download, Paperclip, Upload } from "lucide-react";
import {
  archiveCapexAttachment,
  downloadCapexAttachment,
  listCapexInvestmentAttachments,
  uploadCapexInvestmentAttachment,
} from "../api/budgetPlanningApi";
import { HttpRequestError } from "../api/httpClient";
import type { CapexInvestmentAttachment } from "../types/budgetPlanning";
import { formatBytes } from "../utils/documentUpload";
import {
  CAPEX_ATTACHMENT_TYPE_OPTIONS,
  attachmentTypeLabel,
  formatAttachmentDate,
  mapCapexAttachmentError,
  newAttachmentIdempotencyKey,
  triggerBrowserDownload,
  uploadStatusLabel,
  validateAttachmentUploadForm,
  type CapexAttachmentUploadUiState,
} from "../utils/capexAttachments";
import { LoadingActivityCard, SectionCard, StateBox } from "./uiKit";

type CapexInvestmentAttachmentsPanelProps = {
  investmentId: string | null;
  readOnly?: boolean;
};

export function CapexInvestmentAttachmentsPanel({
  investmentId,
  readOnly = false,
}: CapexInvestmentAttachmentsPanelProps) {
  const [items, setItems] = useState<CapexInvestmentAttachment[]>([]);
  const [loading, setLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [feedbackVariant, setFeedbackVariant] = useState<"success" | "error">("success");

  const [file, setFile] = useState<File | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [attachmentType, setAttachmentType] = useState("");
  const [description, setDescription] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState(newAttachmentIdempotencyKey);
  const [uploadState, setUploadState] = useState<CapexAttachmentUploadUiState>("ready");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [formError, setFormError] = useState<string | null>(null);

  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [archivingId, setArchivingId] = useState<string | null>(null);
  const uploadingRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const loadList = useCallback(
    async (signal?: AbortSignal) => {
      if (!investmentId) {
        setItems([]);
        return;
      }
      setLoading(true);
      setListError(null);
      try {
        const rows = await listCapexInvestmentAttachments(investmentId, signal);
        if (signal?.aborted) return;
        setItems(rows);
      } catch (err: unknown) {
        if (signal?.aborted) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setListError("Sessão expirada. Faça login novamente.");
        } else if (err instanceof HttpRequestError && err.status === 403) {
          setListError("Acesso negado aos anexos deste investimento.");
        } else {
          setListError(mapCapexAttachmentError(err));
        }
        setItems([]);
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [investmentId],
  );

  useEffect(() => {
    if (!investmentId) {
      setItems([]);
      setListError(null);
      return;
    }
    const controller = new AbortController();
    void loadList(controller.signal);
    return () => controller.abort();
  }, [investmentId, loadList]);

  function resetUploadForm() {
    setFile(null);
    setDisplayName("");
    setAttachmentType("");
    setDescription("");
    setUploadProgress(0);
    setUploadState("ready");
    setFormError(null);
    setIdempotencyKey(newAttachmentIdempotencyKey());
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function onFileSelected(next: File | null) {
    setFile(next);
    setIdempotencyKey(newAttachmentIdempotencyKey());
    setUploadState("ready");
    setFormError(null);
    setUploadProgress(0);
    if (next && !displayName.trim()) {
      setDisplayName(next.name.replace(/\.[^.]+$/, "") || next.name);
    }
  }

  function cancelUploadForm() {
    if (uploadingRef.current) return;
    resetUploadForm();
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (!investmentId || readOnly || uploadingRef.current) return;

    const validation = validateAttachmentUploadForm({
      file,
      displayName,
      attachmentType,
    });
    if (!validation.ok) {
      setFormError(validation.message);
      setUploadState("error");
      return;
    }
    if (!file) return;

    uploadingRef.current = true;
    setFormError(null);
    setFeedback(null);
    setUploadState("uploading");
    setUploadProgress(0);

    try {
      await uploadCapexInvestmentAttachment(
        {
          investmentId,
          file,
          attachmentType,
          displayName: displayName.trim(),
          description: description.trim() || undefined,
          idempotencyKey,
        },
        {
          onProgress: (ratio) => {
            setUploadProgress(ratio);
            if (ratio >= 0.999) {
              setUploadState("processing");
            } else {
              setUploadState("uploading");
            }
          },
        },
      );
      setUploadState("done");
      setFeedback("Anexo enviado com sucesso.");
      setFeedbackVariant("success");
      resetUploadForm();
      await loadList();
    } catch (err: unknown) {
      setUploadState("error");
      setFormError(mapCapexAttachmentError(err));
    } finally {
      uploadingRef.current = false;
    }
  }

  async function handleDownload(row: CapexInvestmentAttachment) {
    if (downloadingId) return;
    setDownloadingId(row.id);
    setFeedback(null);
    try {
      const blob = await downloadCapexAttachment(row.id);
      triggerBrowserDownload(blob, row.original_filename || row.display_name || "anexo");
    } catch (err: unknown) {
      setFeedback(mapCapexAttachmentError(err));
      setFeedbackVariant("error");
    } finally {
      setDownloadingId(null);
    }
  }

  async function handleArchive(row: CapexInvestmentAttachment) {
    if (readOnly || archivingId) return;
    const ok = window.confirm(
      "Arquivar este anexo? Ele deixará de aparecer na lista ativa, mas permanecerá registrado para auditoria.",
    );
    if (!ok) return;
    setArchivingId(row.id);
    setFeedback(null);
    try {
      await archiveCapexAttachment(row.id);
      setFeedback("Anexo arquivado.");
      setFeedbackVariant("success");
      await loadList();
    } catch (err: unknown) {
      setFeedback(mapCapexAttachmentError(err));
      setFeedbackVariant("error");
    } finally {
      setArchivingId(null);
    }
  }

  if (!investmentId) {
    return (
      <SectionCard title="Documentos e Anexos" hint="Anexos só após o primeiro salvamento do rascunho.">
        <StateBox variant="default" dismissible={false}>
          Salve o rascunho para adicionar documentos.
        </StateBox>
      </SectionCard>
    );
  }

  const busyUpload = uploadState === "uploading" || uploadState === "processing";

  return (
    <SectionCard
      title="Documentos e Anexos"
      hint={
        readOnly
          ? "Investimento arquivado — anexos em somente leitura."
          : "Upload multipart autenticado (máx. 25 MB). O caminho físico não é exposto."
      }
    >
      {feedback ? (
        <StateBox variant={feedbackVariant} dismissible={false}>
          {feedback}
        </StateBox>
      ) : null}

      {listError ? (
        <StateBox variant="error" dismissible={false}>
          {listError}
        </StateBox>
      ) : null}

      {loading ? <LoadingActivityCard title="Carregando anexos…" variant="panel" /> : null}

      {!loading && items.length === 0 && !listError ? (
        <p className="po-muted" data-testid="capex-attachments-empty">
          Nenhum documento foi anexado a este investimento.
        </p>
      ) : null}

      {!loading && items.length > 0 ? (
        <ul className="po-doc-list" data-testid="capex-attachments-list">
          {items.map((row) => (
            <li key={row.id}>
              <div className="po-doc-list__meta">
                <Paperclip size={18} aria-hidden="true" />
                <div>
                  <strong>{row.display_name}</strong>
                  <span className="po-muted">
                    {attachmentTypeLabel(row.attachment_type)}
                    {row.description ? ` · ${row.description}` : ""}
                  </span>
                  <span className="po-muted">
                    {row.original_filename} · {formatBytes(row.file_size)} ·{" "}
                    {formatAttachmentDate(row.created_at)}
                    {row.created_by ? ` · ${row.created_by}` : ""}
                  </span>
                </div>
              </div>
              <div className="po-form-actions">
                <button
                  type="button"
                  className="po-btn po-btn--secondary"
                  disabled={downloadingId === row.id}
                  onClick={() => void handleDownload(row)}
                >
                  <Download size={16} aria-hidden="true" />
                  {downloadingId === row.id ? "Baixando…" : "Baixar"}
                </button>
                {!readOnly ? (
                  <button
                    type="button"
                    className="po-btn po-btn--secondary"
                    disabled={archivingId === row.id}
                    onClick={() => void handleArchive(row)}
                  >
                    <Archive size={16} aria-hidden="true" />
                    {archivingId === row.id ? "Arquivando…" : "Arquivar"}
                  </button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      {!readOnly ? (
        <form
          className="po-form po-attachment-upload"
          data-testid="capex-attachment-upload-form"
          onSubmit={(e) => void handleUpload(e)}
        >
          <h3 className="po-attachment-upload__title">Enviar anexo</h3>
          <label>
            Arquivo
            <input
              ref={fileInputRef}
              type="file"
              disabled={busyUpload}
              onChange={(e) => onFileSelected(e.target.files?.[0] ?? null)}
            />
          </label>
          <label>
            Nome de exibição
            <input
              required
              value={displayName}
              disabled={busyUpload}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </label>
          <label>
            Tipo
            <select
              required
              value={attachmentType}
              disabled={busyUpload}
              onChange={(e) => setAttachmentType(e.target.value)}
            >
              <option value="">Selecione…</option>
              {CAPEX_ATTACHMENT_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Descrição (opcional)
            <input
              value={description}
              disabled={busyUpload}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>

          <p className="po-muted" aria-live="polite">
            {file
              ? `Selecionado: ${file.name} (${formatBytes(file.size)}) — ${uploadStatusLabel(uploadState)}`
              : `Nenhum arquivo selecionado — ${uploadStatusLabel(uploadState)}`}
            {busyUpload ? ` · ${Math.round(uploadProgress * 100)}%` : ""}
          </p>

          {busyUpload ? (
            <div
              className="po-upload-progress"
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(uploadProgress * 100)}
            >
              <div
                className="po-upload-progress__bar"
                style={{ width: `${Math.round(uploadProgress * 100)}%` }}
              />
            </div>
          ) : null}

          {formError ? (
            <StateBox variant="error" dismissible={false}>
              {formError}
            </StateBox>
          ) : null}

          <div className="po-form-actions">
            <button
              type="submit"
              className="po-btn po-btn--primary"
              disabled={busyUpload || !file}
            >
              <Upload size={16} aria-hidden="true" />
              {busyUpload ? "Enviando…" : "Enviar anexo"}
            </button>
            <button
              type="button"
              className="po-btn po-btn--secondary"
              disabled={busyUpload}
              onClick={cancelUploadForm}
            >
              Cancelar
            </button>
          </div>
        </form>
      ) : null}
    </SectionCard>
  );
}
