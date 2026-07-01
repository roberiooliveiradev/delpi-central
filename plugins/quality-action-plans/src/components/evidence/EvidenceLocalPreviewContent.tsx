import { useEffect, useRef, useState } from "react";

import { formatEvidenceFileSize } from "./evidenceAttachmentUtils";
import {
  canPreviewLocalFile,
  resolveLocalFilePreviewMode,
} from "./evidencePreviewUtils";
import { parseSpreadsheetPreview, type SpreadsheetPreviewData } from "./spreadsheetPreviewModel";
import { SpreadsheetPreview } from "./SpreadsheetPreview";
import { parseDocxPreview, type DocxPreviewData } from "./docxPreviewModel";
import { DocxPreview } from "./DocxPreview";

type Props = {
  file: File;
};

export function EvidenceLocalPreviewContent({ file }: Props) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [spreadsheetData, setSpreadsheetData] = useState<SpreadsheetPreviewData | null>(null);
  const [docxData, setDocxData] = useState<DocxPreviewData | null>(null);
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
      setSpreadsheetData(null);
      setDocxData(null);

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

        if (mode === "spreadsheet") {
          const data = await parseSpreadsheetPreview(file, { fileName: file.name });
          if (cancelled) return;
          setSpreadsheetData(data);
          return;
        }

        if (mode === "docx") {
          const data = await parseDocxPreview(file);
          if (cancelled) return;
          setDocxData(data);
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

        setError("Pré-visualização não disponível para este tipo de arquivo.");
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

  if (spreadsheetData) {
    return <SpreadsheetPreview data={spreadsheetData} />;
  }

  if (docxData) {
    return <DocxPreview data={docxData} title={file.name} />;
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
