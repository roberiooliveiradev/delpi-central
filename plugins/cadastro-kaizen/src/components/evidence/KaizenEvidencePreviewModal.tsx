import { useEffect, useRef, useState } from "react";

import { fetchKaizenEvidenceObjectUrl } from "../../api/kaizenApi";
import type { KaizenEvidence } from "../../types/kaizen";
import { Modal } from "../ui/Modal";
import { formatEvidenceFileSize } from "./kaizenEvidenceUtils";
import {
  evidencePreviewTitle,
  resolveEvidencePreviewMode,
  resolveLocalFilePreviewMode,
  type EvidencePreviewMode,
} from "./kaizenEvidencePreview";

type SavedSource = { kind: "saved"; kaizenId: string; evidence: KaizenEvidence };
type LocalSource = { kind: "local"; file: File };
export type EvidencePreviewSource = SavedSource | LocalSource;

type Props = {
  source: EvidencePreviewSource | null;
  onClose: () => void;
};

function sourceTitle(source: EvidencePreviewSource): string {
  return source.kind === "saved" ? evidencePreviewTitle(source.evidence) : source.file.name;
}

function sourceMode(source: EvidencePreviewSource): EvidencePreviewMode {
  return source.kind === "saved"
    ? resolveEvidencePreviewMode(source.evidence)
    : resolveLocalFilePreviewMode(source.file);
}

function sourceSize(source: EvidencePreviewSource): number | null | undefined {
  return source.kind === "saved" ? source.evidence.size_bytes : source.file.size;
}

export function KaizenEvidencePreviewModal({ source, onClose }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  const mode = source ? sourceMode(source) : "none";

  useEffect(() => {
    let cancelled = false;

    function cleanup() {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    }

    async function load() {
      cleanup();
      setUrl(null);
      setError(null);
      if (!source || mode === "none") return;

      setLoading(true);
      try {
        if (source.kind === "local") {
          const objectUrl = URL.createObjectURL(source.file);
          if (cancelled) {
            URL.revokeObjectURL(objectUrl);
            return;
          }
          objectUrlRef.current = objectUrl;
          setUrl(objectUrl);
        } else {
          const objectUrl = await fetchKaizenEvidenceObjectUrl(source.kaizenId, source.evidence.id);
          if (cancelled) {
            URL.revokeObjectURL(objectUrl);
            return;
          }
          objectUrlRef.current = objectUrl;
          setUrl(objectUrl);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Não foi possível carregar a pré-visualização.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();

    return () => {
      cancelled = true;
      cleanup();
    };
  }, [source, mode]);

  const title = source ? sourceTitle(source) : "Pré-visualização";

  return (
    <Modal
      open={source != null}
      title={title}
      className="kz-modal--preview"
      onClose={onClose}
    >
      <div className="kz-evidence-preview">
        {loading ? (
          <p className="kz-empty-hint kz-evidence-preview__status">Carregando pré-visualização…</p>
        ) : error ? (
          <p className="kz-empty-hint kz-evidence-preview__status">{error}</p>
        ) : mode === "image" && url ? (
          <img className="kz-evidence-preview__image" src={url} alt={title} />
        ) : mode === "pdf" && url ? (
          <iframe className="kz-evidence-preview__pdf" src={url} title={`Pré-visualização: ${title}`} />
        ) : (
          <p className="kz-empty-hint kz-evidence-preview__status">
            Pré-visualização não disponível para este tipo de arquivo. Use o download.
          </p>
        )}

        {source ? (
          <div className="kz-evidence-preview__meta">
            <span>{source.kind === "saved" ? source.evidence.file_name ?? "Arquivo" : source.file.name}</span>
            <span>{formatEvidenceFileSize(sourceSize(source))}</span>
          </div>
        ) : null}
      </div>
    </Modal>
  );
}
