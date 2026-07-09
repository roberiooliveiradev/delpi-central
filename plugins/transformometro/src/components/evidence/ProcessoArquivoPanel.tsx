import { useCallback, useEffect, useState } from "react";
import type { MouseEvent } from "react";
import { Download, Eye, FileText, LinkIcon, Plus, Trash2, Upload } from "lucide-react";

import { EvidenceDropzone } from "./EvidenceDropzone";
import {
  EvidenceFilePreviewModal,
  isImageMime,
  isPdfMime,
} from "./EvidenceFilePreviewModal";
import { PendingUploadCards, type PendingUploadItem } from "./PendingUploadCards";
import {
  canPreviewProcessoArquivo,
  createPendingUploadId,
  deleteProcessoArquivo,
  fetchProcessoArquivoObjectUrl,
  fetchProcessoArquivos,
  formatEvidenceFileSize,
  inferProcessoArquivoTypeFromFile,
  uploadProcessoArquivo,
} from "../../data/api/transformometroProcessoArquivoApi";
import { FieldLabel } from "@delpi/plugin-ui";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { ProcessoArquivo } from "../../types/processoArquivo";
import { isSpreadsheetAttachedFile } from "../../utils/evidenceFilePreview";
import { useConfirm } from "../ui/ConfirmDialogProvider";

const P = TM_HELP_TOOLTIPS.processos;

type PendingUpload = PendingUploadItem;

type Props = {
  processoId: string;
  getAccessToken?: () => string | undefined;
  resyncVersion?: number;
  onError: (message: string | null) => void;
  onChanged?: () => void;
  readOnly?: boolean;
  hideHeader?: boolean;
};

function ArquivoThumb({
  processoId,
  arquivo,
  getAccessToken,
}: {
  processoId: string;
  arquivo: ProcessoArquivo;
  getAccessToken?: () => string | undefined;
}) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    let revoked: string | null = null;
    let active = true;
    if (isImageMime(arquivo.tipo_mime) || isPdfMime(arquivo.tipo_mime)) {
      fetchProcessoArquivoObjectUrl(processoId, arquivo.arquivo_id, getAccessToken)
        .then((url) => {
          if (active) {
            revoked = url;
            setObjectUrl(url);
          } else {
            URL.revokeObjectURL(url);
          }
        })
        .catch(() => undefined);
    }
    return () => {
      active = false;
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [processoId, arquivo.arquivo_id, arquivo.tipo_mime, getAccessToken]);

  if (arquivo.tipo === "link") {
    return (
      <a
        className="tm-evidence__link"
        href={arquivo.url_externa ?? "#"}
        target="_blank"
        rel="noreferrer"
      >
        <LinkIcon size={20} aria-hidden="true" />
      </a>
    );
  }

  if (isImageMime(arquivo.tipo_mime)) {
    return objectUrl ? (
      <img
        className="tm-evidence__img"
        src={objectUrl}
        alt={arquivo.descricao ?? arquivo.nome_arquivo ?? "Arquivo"}
      />
    ) : (
      <div className="tm-evidence__img tm-evidence__img--loading" aria-hidden="true" />
    );
  }

  if (isPdfMime(arquivo.tipo_mime)) {
    return objectUrl ? (
      <iframe
        className="tm-evidence__pdf-thumb"
        src={objectUrl}
        title={arquivo.descricao ?? arquivo.nome_arquivo ?? "Arquivo PDF"}
        tabIndex={-1}
      />
    ) : (
      <div className="tm-evidence__img tm-evidence__img--loading" aria-hidden="true" />
    );
  }

  if (isSpreadsheetAttachedFile(arquivo)) {
    return (
      <div className="tm-evidence__file-icon tm-evidence__file-icon--spreadsheet" aria-hidden="true">
        <FileText size={24} />
        <span>XLSX</span>
      </div>
    );
  }

  return (
    <div className="tm-evidence__file-icon" aria-hidden="true">
      <FileText size={24} />
    </div>
  );
}

async function downloadArquivo(
  processoId: string,
  arquivo: ProcessoArquivo,
  getAccessToken?: () => string | undefined
) {
  try {
    const url = await fetchProcessoArquivoObjectUrl(
      processoId,
      arquivo.arquivo_id,
      getAccessToken
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = arquivo.nome_arquivo ?? "arquivo";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  } catch {
    // download falhou — preview autenticado exige token; não abrir URL direta da API
  }
}

function ArquivoCard({
  processoId,
  arquivo,
  readOnly,
  getAccessToken,
  onDelete,
  onPreviewError,
}: {
  processoId: string;
  arquivo: ProcessoArquivo;
  readOnly: boolean;
  getAccessToken?: () => string | undefined;
  onDelete: (arquivo: ProcessoArquivo) => void;
  onPreviewError: (message: string) => void;
}) {
  const previewable = canPreviewProcessoArquivo(arquivo);
  const [previewOpen, setPreviewOpen] = useState(false);

  const fetchPreviewUrl = useCallback(
    () => fetchProcessoArquivoObjectUrl(processoId, arquivo.arquivo_id, getAccessToken),
    [processoId, arquivo.arquivo_id, getAccessToken]
  );

  function handlePreview(event?: MouseEvent<HTMLElement>) {
    event?.stopPropagation();
    if (arquivo.tipo === "link" && arquivo.url_externa) {
      window.open(arquivo.url_externa, "_blank", "noopener,noreferrer");
      return;
    }
    if (previewable) {
      setPreviewOpen(true);
    }
  }

  return (
    <figure className="tm-evidence">
      {previewable ? (
        <button
          type="button"
          className="tm-evidence__thumb-btn"
          onClick={(event) => handlePreview(event)}
          aria-label={`Pré-visualizar ${arquivo.nome_arquivo ?? "arquivo"}`}
        >
          <ArquivoThumb
            processoId={processoId}
            arquivo={arquivo}
            getAccessToken={getAccessToken}
          />
        </button>
      ) : (
        <ArquivoThumb processoId={processoId} arquivo={arquivo} getAccessToken={getAccessToken} />
      )}
      <figcaption className="tm-evidence__caption">
        <span>{arquivo.descricao || arquivo.nome_arquivo || "Arquivo"}</span>
        {arquivo.tamanho_bytes ? (
          <span className="tm-evidence__size">{formatEvidenceFileSize(arquivo.tamanho_bytes)}</span>
        ) : null}
      </figcaption>
      <div className="tm-evidence__actions">
        {previewable || arquivo.tipo === "link" ? (
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={(event) => handlePreview(event)}
            aria-label="Abrir arquivo"
          >
            <Eye size={12} aria-hidden="true" />
          </button>
        ) : null}
        {arquivo.tipo !== "link" ? (
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={() => void downloadArquivo(processoId, arquivo, getAccessToken)}
            aria-label="Baixar arquivo"
          >
            <Download size={12} aria-hidden="true" />
          </button>
        ) : null}
        {!readOnly ? (
          <button
            type="button"
            className="ds-danger-btn"
            onClick={() => onDelete(arquivo)}
            aria-label="Excluir arquivo"
          >
            <Trash2 size={12} aria-hidden="true" />
          </button>
        ) : null}
      </div>
      <EvidenceFilePreviewModal
        open={previewOpen}
        title={arquivo.descricao || arquivo.nome_arquivo || "Arquivo"}
        mime={arquivo.tipo_mime}
        fetchObjectUrl={fetchPreviewUrl}
        onClose={() => setPreviewOpen(false)}
        onError={onPreviewError}
        metaItems={[
          arquivo.tipo_mime ?? arquivo.tipo,
          formatEvidenceFileSize(arquivo.tamanho_bytes),
        ]}
      />
    </figure>
  );
}

export function ProcessoArquivoPanel({
  processoId,
  getAccessToken,
  resyncVersion = 0,
  onError,
  onChanged,
  readOnly = false,
  hideHeader = false,
}: Props) {
  const confirm = useConfirm();
  const [arquivos, setArquivos] = useState<ProcessoArquivo[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [pending, setPending] = useState<PendingUpload[]>([]);
  const [showLink, setShowLink] = useState(false);
  const [externalUrl, setExternalUrl] = useState("");
  const [linkDescription, setLinkDescription] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const items = await fetchProcessoArquivos(processoId, getAccessToken);
      setArquivos(items);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao listar arquivos do processo.");
    } finally {
      setLoading(false);
    }
  }, [processoId, getAccessToken, onError]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  function addFiles(files: File[]) {
    if (!files.length || uploading) return;
    onError(null);
    setPending((current) => [
      ...current,
      ...files.map((file) => ({
        id: createPendingUploadId(),
        file,
        descricao: "",
      })),
    ]);
  }

  function updatePending(id: string, descricao: string) {
    setPending((current) =>
      current.map((item) => (item.id === id ? { ...item, descricao } : item))
    );
  }

  function removePending(id: string) {
    setPending((current) => current.filter((item) => item.id !== id));
  }

  async function handleUploadQueue() {
    if (!pending.length || uploading) return;
    setUploading(true);
    onError(null);
    try {
      for (const item of pending) {
        await uploadProcessoArquivo(
          processoId,
          {
            tipo: inferProcessoArquivoTypeFromFile(item.file),
            file: item.file,
            descricao: item.descricao.trim() || undefined,
          },
          getAccessToken
        );
      }
      setPending([]);
      await load();
      onChanged?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao anexar arquivos.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAddLink() {
    if (!externalUrl.trim() || uploading) return;
    setUploading(true);
    onError(null);
    try {
      await uploadProcessoArquivo(
        processoId,
        {
          tipo: "link",
          urlExterna: externalUrl.trim(),
          descricao: linkDescription.trim() || undefined,
        },
        getAccessToken
      );
      setExternalUrl("");
      setLinkDescription("");
      setShowLink(false);
      await load();
      onChanged?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao anexar link.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(arquivo: ProcessoArquivo) {
    const confirmed = await confirm({
      title: "Excluir arquivo",
      message: "Excluir este arquivo do processo?",
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    onError(null);
    try {
      await deleteProcessoArquivo(processoId, arquivo.arquivo_id, getAccessToken);
      await load();
      onChanged?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao excluir arquivo.");
    }
  }

  return (
    <section
      className={[
        "ds-cadastro-section",
        "ds-cadastro-section--embedded",
        "tm-evidence-panel",
        hideHeader ? "tm-evidence-panel--no-header" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {hideHeader ? null : (
        <header className="ds-cadastro-section__header">
          <h3 className="ds-section-title">Arquivos do processo</h3>
          {arquivos.length ? (
            <span className="ds-cadastro-section__badge">{arquivos.length}</span>
          ) : null}
        </header>
      )}

      {loading ? <p className="ds-hint">Carregando arquivos…</p> : null}

      {!loading && arquivos.length === 0 ? (
        <p className="ds-hint">Nenhum arquivo anexado a este processo.</p>
      ) : null}

      <div className="tm-evidence-grid">
        {arquivos.map((arquivo) => (
          <ArquivoCard
            key={arquivo.arquivo_id}
            processoId={processoId}
            arquivo={arquivo}
            readOnly={readOnly}
            getAccessToken={getAccessToken}
            onDelete={(item) => void handleDelete(item)}
            onPreviewError={onError}
          />
        ))}
      </div>

      {!readOnly ? (
        <div className="tm-evidence-upload">
          <EvidenceDropzone disabled={uploading} onFilesSelected={addFiles} />

          {pending.length ? (
            <PendingUploadCards
              items={pending}
              disabled={uploading}
              onUpdateDescription={updatePending}
              onRemove={removePending}
            />
          ) : null}

          {pending.length ? (
            <div className="tm-evidence-upload__submit">
              <button
                type="button"
                className="ds-primary-btn"
                onClick={() => void handleUploadQueue()}
                disabled={uploading}
              >
                <Upload size={14} aria-hidden="true" />
                {uploading
                  ? "Enviando…"
                  : pending.length > 1
                    ? `Enviar ${pending.length} arquivos`
                    : "Enviar arquivo"}
              </button>
            </div>
          ) : null}

          {showLink ? (
            <div className="tm-evidence-link">
              <div className="ds-field">
                <label htmlFor="tm-proc-arq-url">
                  <FieldLabel className="tm-field__label" label="URL" hint={P.arquivoUrl} />
                </label>
                <input
                  id="tm-proc-arq-url"
                  type="url"
                  placeholder="https://…"
                  value={externalUrl}
                  disabled={uploading}
                  onChange={(event) => setExternalUrl(event.target.value)}
                />
              </div>
              <div className="ds-field">
                <label htmlFor="tm-proc-arq-desc">
                  <FieldLabel className="tm-field__label" label="Descrição" hint={P.arquivoDescription} />
                </label>
                <input
                  id="tm-proc-arq-desc"
                  value={linkDescription}
                  disabled={uploading}
                  onChange={(event) => setLinkDescription(event.target.value)}
                />
              </div>
              <button
                type="button"
                className="ds-primary-btn"
                onClick={() => void handleAddLink()}
                disabled={uploading || externalUrl.trim().length === 0}
              >
                <LinkIcon size={14} aria-hidden="true" />
                {uploading ? "Enviando…" : "Anexar link"}
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="ds-ghost-btn tm-evidence-upload__link-toggle"
              onClick={() => setShowLink(true)}
            >
              <Plus size={14} aria-hidden="true" />
              Adicionar por link externo
            </button>
          )}
        </div>
      ) : null}
    </section>
  );
}
