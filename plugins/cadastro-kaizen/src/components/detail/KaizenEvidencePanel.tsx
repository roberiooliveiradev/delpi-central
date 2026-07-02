import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, FileText, LinkIcon, Plus, Trash2, Upload } from "lucide-react";

import {
  deleteKaizenEvidence,
  fetchKaizenEvidenceObjectUrl,
  fetchKaizenEvidences,
  kaizenEvidenceFileUrl,
  uploadKaizenEvidence,
} from "../../api/kaizenApi";
import type {
  KaizenEvidence,
  KaizenEvidenceStage,
  KaizenEvidenceType,
} from "../../types/kaizen";
import { StateAlert } from "../StateAlert";
import { HelpTooltip } from "../ui/HelpTooltip";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { KaizenEvidenceDropzone } from "../evidence/KaizenEvidenceDropzone";
import {
  KaizenEvidencePendingList,
  type KaizenPendingUpload,
} from "../evidence/KaizenEvidencePendingList";
import {
  createPendingUploadId,
  inferEvidenceTypeFromFile,
} from "../evidence/kaizenEvidenceUtils";

type KaizenEvidencePanelProps = {
  kaizenId: string;
  readOnly: boolean;
};

const STAGE_LABELS: Record<KaizenEvidenceStage, string> = {
  antes: "Antes",
  depois: "Depois",
  geral: "Gerais",
};

function isImage(mime: string | null): boolean {
  return !!mime && mime.startsWith("image/");
}

function EvidenceThumb({
  kaizenId,
  evidence,
}: {
  kaizenId: string;
  evidence: KaizenEvidence;
}) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    let revoked: string | null = null;
    let active = true;
    if (isImage(evidence.mime_type)) {
      fetchKaizenEvidenceObjectUrl(kaizenId, evidence.id)
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
  }, [kaizenId, evidence.id, evidence.mime_type]);

  if (evidence.type === "link") {
    return (
      <a
        className="kz-evidence__link"
        href={evidence.external_url ?? "#"}
        target="_blank"
        rel="noreferrer"
      >
        <LinkIcon size={20} aria-hidden="true" />
      </a>
    );
  }

  if (isImage(evidence.mime_type)) {
    return objectUrl ? (
      <img className="kz-evidence__img" src={objectUrl} alt={evidence.description ?? evidence.file_name ?? "Evidência"} />
    ) : (
      <div className="kz-evidence__img kz-evidence__img--loading" aria-hidden="true" />
    );
  }

  return (
    <div className="kz-evidence__file-icon" aria-hidden="true">
      <FileText size={24} />
    </div>
  );
}

async function downloadEvidence(kaizenId: string, evidence: KaizenEvidence) {
  try {
    const url = await fetchKaizenEvidenceObjectUrl(kaizenId, evidence.id);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = evidence.file_name ?? "evidencia";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  } catch {
    window.open(kaizenEvidenceFileUrl(kaizenId, evidence.id), "_blank");
  }
}

export function KaizenEvidencePanel({ kaizenId, readOnly }: KaizenEvidencePanelProps) {
  const [evidences, setEvidences] = useState<KaizenEvidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const [pending, setPending] = useState<KaizenPendingUpload[]>([]);
  const [defaultStage, setDefaultStage] = useState<KaizenEvidenceStage>("antes");

  const [showLink, setShowLink] = useState(false);
  const [linkStage, setLinkStage] = useState<KaizenEvidenceStage>("geral");
  const [externalUrl, setExternalUrl] = useState("");
  const [linkDescription, setLinkDescription] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setEvidences(await fetchKaizenEvidences(kaizenId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao listar evidências.");
    } finally {
      setLoading(false);
    }
  }, [kaizenId]);

  useEffect(() => {
    void load();
  }, [load]);

  const grouped = useMemo(() => {
    const groups: Record<KaizenEvidenceStage, KaizenEvidence[]> = {
      antes: [],
      depois: [],
      geral: [],
    };
    for (const evidence of evidences) {
      groups[evidence.stage].push(evidence);
    }
    return groups;
  }, [evidences]);

  function addFiles(files: File[]) {
    if (!files.length || uploading) return;
    setError(null);
    setPending((current) => [
      ...current,
      ...files.map((file) => ({
        id: createPendingUploadId(),
        file,
        stage: defaultStage,
        description: "",
      })),
    ]);
  }

  function updatePending(id: string, patch: Partial<KaizenPendingUpload>) {
    setPending((current) => current.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  function removePending(id: string) {
    setPending((current) => current.filter((item) => item.id !== id));
  }

  async function handleUploadQueue() {
    if (!pending.length || uploading) return;
    setUploading(true);
    setError(null);
    try {
      for (const item of pending) {
        const type: KaizenEvidenceType = inferEvidenceTypeFromFile(item.file);
        await uploadKaizenEvidence(kaizenId, {
          stage: item.stage,
          type,
          file: item.file,
          description: item.description.trim() || undefined,
        });
      }
      setPending([]);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao anexar evidências.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAddLink() {
    if (!externalUrl.trim() || uploading) return;
    setUploading(true);
    setError(null);
    try {
      await uploadKaizenEvidence(kaizenId, {
        stage: linkStage,
        type: "link",
        externalUrl: externalUrl.trim(),
        description: linkDescription.trim() || undefined,
      });
      setExternalUrl("");
      setLinkDescription("");
      setShowLink(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao anexar link.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(evidence: KaizenEvidence) {
    if (!window.confirm("Excluir esta evidência?")) return;
    try {
      await deleteKaizenEvidence(kaizenId, evidence.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir evidência.");
    }
  }

  return (
    <div className="kz-evidence-panel">
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <div className="kz-evidence-gallery">
        {(["antes", "depois"] as KaizenEvidenceStage[]).map((stageKey) => (
          <div className="kz-evidence-column" key={stageKey}>
            <h3 className="kz-evidence-column__title">{STAGE_LABELS[stageKey]}</h3>
            <div className="kz-evidence-column__items">
              {grouped[stageKey].length === 0 ? (
                <p className="kz-empty-hint">Sem registros.</p>
              ) : (
                grouped[stageKey].map((evidence) => (
                  <figure className="kz-evidence" key={evidence.id}>
                    <EvidenceThumb kaizenId={kaizenId} evidence={evidence} />
                    <figcaption className="kz-evidence__caption">
                      {evidence.description || evidence.file_name || "Evidência"}
                    </figcaption>
                    <div className="kz-evidence__actions">
                      {evidence.type !== "link" ? (
                        <button
                          type="button"
                          className="kz-ghost-btn"
                          onClick={() => void downloadEvidence(kaizenId, evidence)}
                        >
                          <Download size={12} aria-hidden="true" />
                        </button>
                      ) : null}
                      {!readOnly ? (
                        <button
                          type="button"
                          className="kz-danger-btn"
                          onClick={() => void handleDelete(evidence)}
                          aria-label="Excluir evidência"
                        >
                          <Trash2 size={12} aria-hidden="true" />
                        </button>
                      ) : null}
                    </div>
                  </figure>
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      {grouped.geral.length > 0 ? (
        <div className="kz-evidence-general">
          <h3 className="kz-evidence-column__title">{STAGE_LABELS.geral}</h3>
          <div className="kz-evidence-column__items kz-evidence-column__items--row">
            {grouped.geral.map((evidence) => (
              <figure className="kz-evidence" key={evidence.id}>
                <EvidenceThumb kaizenId={kaizenId} evidence={evidence} />
                <figcaption className="kz-evidence__caption">
                  {evidence.description || evidence.file_name || "Evidência"}
                </figcaption>
                <div className="kz-evidence__actions">
                  {evidence.type !== "link" ? (
                    <button
                      type="button"
                      className="kz-ghost-btn"
                      onClick={() => void downloadEvidence(kaizenId, evidence)}
                    >
                      <Download size={12} aria-hidden="true" />
                    </button>
                  ) : null}
                  {!readOnly ? (
                    <button
                      type="button"
                      className="kz-danger-btn"
                      onClick={() => void handleDelete(evidence)}
                      aria-label="Excluir evidência"
                    >
                      <Trash2 size={12} aria-hidden="true" />
                    </button>
                  ) : null}
                </div>
              </figure>
            ))}
          </div>
        </div>
      ) : null}

      {loading ? <p className="kz-empty-hint">Carregando evidências…</p> : null}

      {!readOnly ? (
        <div className="kz-evidence-upload">
          <div className="kz-evidence-upload__head">
            <span className="kz-evidence-upload__title">
              Adicionar evidências
              <HelpTooltip
                content={KAIZEN_HELP_TOOLTIPS.evidence.upload}
                ariaLabel="Ajuda: enviar evidências"
              />
            </span>
            <label className="kz-evidence-upload__default-stage">
              Etapa padrão
              <select
                value={defaultStage}
                disabled={uploading}
                onChange={(event) => setDefaultStage(event.target.value as KaizenEvidenceStage)}
              >
                <option value="antes">Antes</option>
                <option value="depois">Depois</option>
                <option value="geral">Geral</option>
              </select>
            </label>
          </div>

          <KaizenEvidenceDropzone disabled={uploading} onFilesSelected={addFiles} />

          {pending.length ? (
            <>
              <KaizenEvidencePendingList
                items={pending}
                disabled={uploading}
                onChange={updatePending}
                onRemove={removePending}
              />
              <div className="kz-evidence-upload__submit">
                <button
                  type="button"
                  className="kz-primary-btn"
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
            </>
          ) : null}

          {showLink ? (
            <div className="kz-evidence-link">
              <div className="kz-field">
                <label htmlFor="kz-ev-link-stage">Etapa</label>
                <select
                  id="kz-ev-link-stage"
                  value={linkStage}
                  disabled={uploading}
                  onChange={(event) => setLinkStage(event.target.value as KaizenEvidenceStage)}
                >
                  <option value="antes">Antes</option>
                  <option value="depois">Depois</option>
                  <option value="geral">Geral</option>
                </select>
              </div>
              <div className="kz-field">
                <label htmlFor="kz-ev-url">URL</label>
                <input
                  id="kz-ev-url"
                  type="url"
                  placeholder="https://…"
                  value={externalUrl}
                  disabled={uploading}
                  onChange={(event) => setExternalUrl(event.target.value)}
                />
              </div>
              <div className="kz-field kz-span-2">
                <label htmlFor="kz-ev-link-desc">Descrição</label>
                <input
                  id="kz-ev-link-desc"
                  value={linkDescription}
                  disabled={uploading}
                  onChange={(event) => setLinkDescription(event.target.value)}
                />
              </div>
              <button
                type="button"
                className="kz-primary-btn"
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
              className="kz-ghost-btn kz-evidence-upload__link-toggle"
              onClick={() => setShowLink(true)}
            >
              <Plus size={14} aria-hidden="true" />
              Adicionar por link externo
            </button>
          )}
        </div>
      ) : null}
    </div>
  );
}
