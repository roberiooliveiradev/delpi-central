import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, FileText, LinkIcon, Trash2, Upload } from "lucide-react";

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

  const [stage, setStage] = useState<KaizenEvidenceStage>("antes");
  const [mode, setMode] = useState<"file" | "link">("file");
  const [file, setFile] = useState<File | null>(null);
  const [externalUrl, setExternalUrl] = useState("");
  const [description, setDescription] = useState("");

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

  async function handleUpload() {
    setUploading(true);
    setError(null);
    try {
      const type: KaizenEvidenceType =
        mode === "link" ? "link" : file && isImage(file.type) ? "photo" : "attachment";
      await uploadKaizenEvidence(kaizenId, {
        stage,
        type,
        file: mode === "file" ? file ?? undefined : undefined,
        externalUrl: mode === "link" ? externalUrl : undefined,
        description: description || undefined,
      });
      setFile(null);
      setExternalUrl("");
      setDescription("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao anexar evidência.");
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

  const canUpload = mode === "link" ? externalUrl.trim().length > 0 : file != null;

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
          <div className="kz-field">
            <label htmlFor="kz-ev-stage">Etapa</label>
            <select
              id="kz-ev-stage"
              value={stage}
              onChange={(event) => setStage(event.target.value as KaizenEvidenceStage)}
            >
              <option value="antes">Antes</option>
              <option value="depois">Depois</option>
              <option value="geral">Geral</option>
            </select>
          </div>

          <div className="kz-field">
            <label htmlFor="kz-ev-mode">Tipo</label>
            <select
              id="kz-ev-mode"
              value={mode}
              onChange={(event) => setMode(event.target.value as "file" | "link")}
            >
              <option value="file">Arquivo</option>
              <option value="link">Link</option>
            </select>
          </div>

          {mode === "file" ? (
            <div className="kz-field">
              <label htmlFor="kz-ev-file">Arquivo</label>
              <input
                id="kz-ev-file"
                type="file"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </div>
          ) : (
            <div className="kz-field">
              <label htmlFor="kz-ev-url">URL</label>
              <input
                id="kz-ev-url"
                type="url"
                placeholder="https://…"
                value={externalUrl}
                onChange={(event) => setExternalUrl(event.target.value)}
              />
            </div>
          )}

          <div className="kz-field kz-span-2">
            <label htmlFor="kz-ev-desc">Descrição</label>
            <input
              id="kz-ev-desc"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>

          <button
            type="button"
            className="kz-primary-btn"
            onClick={() => void handleUpload()}
            disabled={uploading || !canUpload}
          >
            <Upload size={14} aria-hidden="true" />
            {uploading ? "Enviando…" : "Anexar evidência"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
