import { useCallback, useEffect, useState } from "react";
import { Download, Eye, FileText, LinkIcon, Plus, Trash2, Upload } from "lucide-react";

import { EvidenceDropzone } from "./EvidenceDropzone";
import {
  canPreviewEvidence,
  createPendingUploadId,
  deleteRevisaoEvidence,
  fetchRevisaoEvidenceObjectUrl,
  fetchRevisaoEvidencias,
  formatEvidenceFileSize,
  inferEvidenceTypeFromFile,
  revisaoEvidenceFileUrl,
  uploadRevisaoEvidence,
} from "../../data/api/transformometroEvidenceApi";
import type { RevisaoEvidence } from "../../types/revisaoEvidence";

type PendingUpload = {
  id: string;
  file: File;
  descricao: string;
};

type Props = {
  revisaoId: string;
  getAccessToken?: () => string | undefined;
  onError: (message: string | null) => void;
  onChanged?: () => void;
  readOnly?: boolean;
};

function isImage(mime: string | null | undefined): boolean {
  return !!mime && mime.startsWith("image/");
}

function EvidenceThumb({
  revisaoId,
  evidence,
  getAccessToken,
}: {
  revisaoId: string;
  evidence: RevisaoEvidence;
  getAccessToken?: () => string | undefined;
}) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    let revoked: string | null = null;
    let active = true;
    if (isImage(evidence.tipo_mime)) {
      fetchRevisaoEvidenceObjectUrl(revisaoId, evidence.evidencia_id, getAccessToken)
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
  }, [revisaoId, evidence.evidencia_id, evidence.tipo_mime, getAccessToken]);

  if (evidence.tipo === "link") {
    return (
      <a
        className="tm-evidence__link"
        href={evidence.url_externa ?? "#"}
        target="_blank"
        rel="noreferrer"
      >
        <LinkIcon size={20} aria-hidden="true" />
      </a>
    );
  }

  if (isImage(evidence.tipo_mime)) {
    return objectUrl ? (
      <img
        className="tm-evidence__img"
        src={objectUrl}
        alt={evidence.descricao ?? evidence.nome_arquivo ?? "Evidência"}
      />
    ) : (
      <div className="tm-evidence__img tm-evidence__img--loading" aria-hidden="true" />
    );
  }

  return (
    <div className="tm-evidence__file-icon" aria-hidden="true">
      <FileText size={24} />
    </div>
  );
}

async function downloadEvidence(
  revisaoId: string,
  evidence: RevisaoEvidence,
  getAccessToken?: () => string | undefined
) {
  try {
    const url = await fetchRevisaoEvidenceObjectUrl(
      revisaoId,
      evidence.evidencia_id,
      getAccessToken
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = evidence.nome_arquivo ?? "evidencia";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  } catch {
    window.open(revisaoEvidenceFileUrl(revisaoId, evidence.evidencia_id), "_blank");
  }
}

function EvidenceCard({
  revisaoId,
  evidence,
  readOnly,
  getAccessToken,
  onDelete,
}: {
  revisaoId: string;
  evidence: RevisaoEvidence;
  readOnly: boolean;
  getAccessToken?: () => string | undefined;
  onDelete: (evidence: RevisaoEvidence) => void;
}) {
  const previewable = canPreviewEvidence(evidence);

  function handlePreview() {
    if (evidence.tipo === "link" && evidence.url_externa) {
      window.open(evidence.url_externa, "_blank");
      return;
    }
    window.open(revisaoEvidenceFileUrl(revisaoId, evidence.evidencia_id), "_blank");
  }

  return (
    <figure className="tm-evidence">
      {previewable ? (
        <button
          type="button"
          className="tm-evidence__thumb-btn"
          onClick={handlePreview}
          aria-label={`Pré-visualizar ${evidence.nome_arquivo ?? "evidência"}`}
        >
          <EvidenceThumb
            revisaoId={revisaoId}
            evidence={evidence}
            getAccessToken={getAccessToken}
          />
        </button>
      ) : (
        <EvidenceThumb revisaoId={revisaoId} evidence={evidence} getAccessToken={getAccessToken} />
      )}
      <figcaption className="tm-evidence__caption">
        <span>{evidence.descricao || evidence.nome_arquivo || "Evidência"}</span>
        {evidence.tamanho_bytes ? (
          <span className="tm-evidence__size">{formatEvidenceFileSize(evidence.tamanho_bytes)}</span>
        ) : null}
      </figcaption>
      <div className="tm-evidence__actions">
        {previewable || evidence.tipo === "link" ? (
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={handlePreview}
            aria-label="Abrir evidência"
          >
            <Eye size={12} aria-hidden="true" />
          </button>
        ) : null}
        {evidence.tipo !== "link" ? (
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={() => void downloadEvidence(revisaoId, evidence, getAccessToken)}
            aria-label="Baixar evidência"
          >
            <Download size={12} aria-hidden="true" />
          </button>
        ) : null}
        {!readOnly ? (
          <button
            type="button"
            className="ds-danger-btn"
            onClick={() => onDelete(evidence)}
            aria-label="Excluir evidência"
          >
            <Trash2 size={12} aria-hidden="true" />
          </button>
        ) : null}
      </div>
    </figure>
  );
}

export function RevisaoEvidencePanel({
  revisaoId,
  getAccessToken,
  onError,
  onChanged,
  readOnly = false,
}: Props) {
  const [evidences, setEvidences] = useState<RevisaoEvidence[]>([]);
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
      const items = await fetchRevisaoEvidencias(revisaoId, getAccessToken);
      setEvidences(items);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao listar evidências.");
    } finally {
      setLoading(false);
    }
  }, [revisaoId, getAccessToken, onError]);

  useEffect(() => {
    void load();
  }, [load]);

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
        await uploadRevisaoEvidence(
          revisaoId,
          {
            tipo: inferEvidenceTypeFromFile(item.file),
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
      onError(err instanceof Error ? err.message : "Erro ao anexar evidências.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAddLink() {
    if (!externalUrl.trim() || uploading) return;
    setUploading(true);
    onError(null);
    try {
      await uploadRevisaoEvidence(
        revisaoId,
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

  async function handleDelete(evidence: RevisaoEvidence) {
    if (!window.confirm("Excluir esta evidência?")) return;
    onError(null);
    try {
      await deleteRevisaoEvidence(revisaoId, evidence.evidencia_id, getAccessToken);
      await load();
      onChanged?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao excluir evidência.");
    }
  }

  return (
    <section className="ds-cadastro-section ds-cadastro-section--embedded tm-evidence-panel">
      <header className="ds-cadastro-section__header">
        <h3 className="ds-section-title">Evidências da revisão</h3>
        {evidences.length ? (
          <span className="ds-cadastro-section__badge">{evidences.length}</span>
        ) : null}
      </header>

      {loading ? <p className="ds-hint">Carregando evidências…</p> : null}

      {!loading && evidences.length === 0 ? (
        <p className="ds-hint">Nenhuma evidência anexada a esta revisão.</p>
      ) : null}

      <div className="tm-evidence-grid">
        {evidences.map((evidence) => (
          <EvidenceCard
            key={evidence.evidencia_id}
            revisaoId={revisaoId}
            evidence={evidence}
            readOnly={readOnly}
            getAccessToken={getAccessToken}
            onDelete={(item) => void handleDelete(item)}
          />
        ))}
      </div>

      {!readOnly ? (
        <div className="tm-evidence-upload">
          <EvidenceDropzone disabled={uploading} onFilesSelected={addFiles} />

          {pending.length ? (
            <ul className="tm-evidence-pending">
              {pending.map((item) => (
                <li key={item.id} className="tm-evidence-pending__item">
                  <span className="tm-evidence-pending__name">{item.file.name}</span>
                  <input
                    type="text"
                    placeholder="Descrição (opcional)"
                    value={item.descricao}
                    disabled={uploading}
                    onChange={(event) => updatePending(item.id, event.target.value)}
                  />
                  <button
                    type="button"
                    className="ds-ghost-btn"
                    disabled={uploading}
                    onClick={() => removePending(item.id)}
                  >
                    Remover
                  </button>
                </li>
              ))}
            </ul>
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
                    ? `Enviar ${pending.length} evidências`
                    : "Enviar evidência"}
              </button>
            </div>
          ) : null}

          {showLink ? (
            <div className="tm-evidence-link">
              <div className="ds-field">
                <label htmlFor="tm-ev-url">URL</label>
                <input
                  id="tm-ev-url"
                  type="url"
                  placeholder="https://…"
                  value={externalUrl}
                  disabled={uploading}
                  onChange={(event) => setExternalUrl(event.target.value)}
                />
              </div>
              <div className="ds-field">
                <label htmlFor="tm-ev-link-desc">Descrição</label>
                <input
                  id="tm-ev-link-desc"
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
