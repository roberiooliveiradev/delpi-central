import { useEffect, useRef, useState } from "react";

import { formatEvidenceFileSize } from "./evidenceAttachmentUtils";
import {
  canPreviewLocalFile,
  resolveLocalFilePreviewMode,
} from "./evidencePreviewUtils";

type Props = {
  file: File;
};

export function EvidenceLocalPreviewContent({ file }: Props) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const mode = resolveLocalFilePreviewMode(file);

  useEffect(() => {
    let cancelled = false;

    async function loadPreview() {
      setLoading(true);
      setError(null);
      setPreviewUrl(null);
      setTextContent(null);

      try {
        if (mode === "image" || mode === "pdf") {
          const url = URL.createObjectURL(file);
          if (cancelled) {
            URL.revokeObjectURL(url);
            return;
          }
          objectUrlRef.current = url;
          setPreviewUrl(url);
          return;
        }

        if (mode === "text") {
          const content = await file.text();
          if (cancelled) return;
          const trimmed = content.trim();
          if (!trimmed) {
            setError("Arquivo de texto vazio.");
            return;
          }
          const max = 80_000;
          setTextContent(
            trimmed.length > max ? `${trimmed.slice(0, max)}\n… (conteúdo truncado)` : trimmed,
          );
          return;
        }

        setError(
          "Prévia local limitada a imagem, PDF e texto. Após enviar, planilhas e documentos Office podem ser visualizados na lista de anexos.",
        );
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Não foi possível carregar a pré-visualização.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadPreview();

    return () => {
      cancelled = true;
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [file, mode]);

  if (loading) {
    return <p className="pac-muted pac-evidence-preview-modal__status">Carregando pré-visualização…</p>;
  }

  if (error) {
    return (
      <div className="pac-evidence-preview-modal__status-wrap">
        <p className="pac-muted pac-evidence-preview-modal__status">{error}</p>
        {!canPreviewLocalFile(file) ? (
          <p className="pac-muted pac-evidence-preview-modal__file-meta">
            {file.name} · {formatEvidenceFileSize(file.size)}
          </p>
        ) : null}
      </div>
    );
  }

  if (mode === "image" && previewUrl) {
    return (
      <img
        src={previewUrl}
        alt={file.name}
        className="pac-evidence-preview-modal__image"
      />
    );
  }

  if (mode === "pdf" && previewUrl) {
    return (
      <iframe
        src={previewUrl}
        title={`Pré-visualização: ${file.name}`}
        className="pac-evidence-preview-modal__pdf"
      />
    );
  }

  if (textContent) {
    return (
      <div className="pac-evidence-preview-modal__text-wrap">
        <pre className="pac-evidence-preview-modal__text">{textContent}</pre>
      </div>
    );
  }

  return (
    <p className="pac-muted pac-evidence-preview-modal__status">
      Pré-visualização não disponível para este arquivo.
    </p>
  );
}
