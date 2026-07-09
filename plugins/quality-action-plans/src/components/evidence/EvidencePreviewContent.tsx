import { useEffect, useMemo, useState } from "react";

import {
  FilePreviewView,
  useFilePreviewLoader,
  type FilePreviewContentState,
} from "@delpi/plugin-ui";

import {
  fetchPlanEvidenceContent,
  fetchPlanEvidenceFileBlob,
} from "../../api/actionPlansApi";
import type { PlanEvidence } from "../../types/rnc8d";
import {
  evidencePreviewTitle,
  resolveEvidencePreviewMode,
} from "./evidencePreviewUtils";

type Props = {
  planId: string;
  evidence: PlanEvidence;
};

export function EvidencePreviewContent({ planId, evidence }: Props) {
  const mode = resolveEvidencePreviewMode(evidence);
  const title = evidencePreviewTitle(evidence);

  const blobSource = useMemo(() => {
    if (mode === "none" || mode === "text") return null;
    return () => fetchPlanEvidenceFileBlob(planId, evidence.id);
  }, [planId, evidence.id, mode]);

  const blobState = useFilePreviewLoader({
    source: blobSource,
    mimeType: evidence.mime_type,
    fileName: evidence.file_name,
    declaredType: evidence.type,
    enabled: mode !== "none" && mode !== "text",
  });

  const [textState, setTextState] = useState<FilePreviewContentState>({
    kind: "text",
    loading: mode === "text",
    error: null,
    previewUrl: null,
    textContent: null,
    textTruncated: false,
    spreadsheetData: null,
    docxData: null,
  });

  useEffect(() => {
    if (mode !== "text") return;

    let cancelled = false;
    setTextState((current) => ({ ...current, loading: true, error: null }));

    void fetchPlanEvidenceContent(planId, evidence.id)
      .then((payload) => {
        if (cancelled) return;
        const content = payload.text_content?.trim();
        if (!content) {
          setTextState({
            kind: "text",
            loading: false,
            error: "Não foi possível extrair texto legível deste arquivo. Use o download.",
            previewUrl: null,
            textContent: null,
            textTruncated: false,
            spreadsheetData: null,
            docxData: null,
          });
          return;
        }
        setTextState({
          kind: "text",
          loading: false,
          error: null,
          previewUrl: null,
          textContent: content,
          textTruncated: Boolean(payload.extraction?.truncated),
          spreadsheetData: null,
          docxData: null,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setTextState({
          kind: "text",
          loading: false,
          error: err instanceof Error ? err.message : "load_failed",
          previewUrl: null,
          textContent: null,
          textTruncated: false,
          spreadsheetData: null,
          docxData: null,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [planId, evidence.id, mode]);

  const state = mode === "text" ? textState : blobState;

  return <FilePreviewView state={state} title={title} />;
}
