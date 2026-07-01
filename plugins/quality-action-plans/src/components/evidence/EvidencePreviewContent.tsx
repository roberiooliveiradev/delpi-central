import { useEffect, useRef, useState } from "react";

import {
  fetchPlanEvidenceContent,
  fetchPlanEvidenceFileBlob,
} from "../../api/actionPlansApi";
import type { PlanEvidence } from "../../types/rnc8d";
import {
  evidencePreviewTitle,
  isImageEvidence,
  isPdfEvidence,
  resolveEvidencePreviewMode,
} from "./evidencePreviewUtils";
import { parseSpreadsheetPreview, type SpreadsheetPreviewData } from "./spreadsheetPreviewModel";
import { SpreadsheetPreview } from "./SpreadsheetPreview";
import { parseDocxPreview, type DocxPreviewData } from "./docxPreviewModel";
import { DocxPreview } from "./DocxPreview";

type Props = {
  planId: string;
  evidence: PlanEvidence;
};

export function EvidencePreviewContent({ planId, evidence }: Props) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [spreadsheetData, setSpreadsheetData] = useState<SpreadsheetPreviewData | null>(null);
  const [docxData, setDocxData] = useState<DocxPreviewData | null>(null);
  const [truncated, setTruncated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const mode = resolveEvidencePreviewMode(evidence);
  const title = evidencePreviewTitle(evidence);

  useEffect(() => {
    let cancelled = false;

    async function loadPreview() {
      setLoading(true);
      setError(null);
      setPreviewUrl(null);
      setTextContent(null);
      setSpreadsheetData(null);
      setDocxData(null);
      setTruncated(false);

      try {
        if (mode === "image" || mode === "pdf") {
          const blob = await fetchPlanEvidenceFileBlob(planId, evidence.id);
          if (cancelled) return;
          const url = URL.createObjectURL(blob);
          objectUrlRef.current = url;
          setPreviewUrl(url);
          return;
        }

        if (mode === "spreadsheet") {
          const blob = await fetchPlanEvidenceFileBlob(planId, evidence.id);
          if (cancelled) return;
          const data = await parseSpreadsheetPreview(blob);
          if (cancelled) return;
          setSpreadsheetData(data);
          return;
        }

        if (mode === "docx") {
          const blob = await fetchPlanEvidenceFileBlob(planId, evidence.id);
          if (cancelled) return;
          const data = await parseDocxPreview(blob);
          if (cancelled) return;
          setDocxData(data);
          return;
        }

        if (mode === "text") {
          const payload = await fetchPlanEvidenceContent(planId, evidence.id);
          if (cancelled) return;
          const content = payload.text_content?.trim();
          if (!content) {
            setError("Não foi possível extrair texto legível deste arquivo. Use o download.");
            return;
          }
          setTextContent(content);
          setTruncated(Boolean(payload.extraction?.truncated));
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
  }, [planId, evidence.id, mode]);

  if (loading) {
    return <p className="pac-muted pac-evidence-preview-modal__status">Carregando pré-visualização…</p>;
  }

  if (error) {
    return <p className="pac-muted pac-evidence-preview-modal__status">{error}</p>;
  }

  if (isImageEvidence(evidence) && previewUrl) {
    return (
      <img
        src={previewUrl}
        alt={title}
        className="pac-evidence-preview-modal__image"
      />
    );
  }

  if (isPdfEvidence(evidence) && previewUrl) {
    return (
      <iframe
        src={previewUrl}
        title={`Pré-visualização: ${title}`}
        className="pac-evidence-preview-modal__pdf"
      />
    );
  }

  if (spreadsheetData) {
    return <SpreadsheetPreview data={spreadsheetData} />;
  }

  if (docxData) {
    return <DocxPreview data={docxData} title={title} />;
  }

  if (textContent) {
    return (
      <div className="pac-evidence-preview-modal__text-wrap">
        <pre className="pac-evidence-preview-modal__text">{textContent}</pre>
        {truncated ? (
          <p className="pac-muted pac-evidence-preview-modal__truncated">
            Conteúdo truncado. Baixe o arquivo para ver o documento completo.
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <p className="pac-muted pac-evidence-preview-modal__status">
      Pré-visualização não disponível para este tipo de arquivo.
    </p>
  );
}
