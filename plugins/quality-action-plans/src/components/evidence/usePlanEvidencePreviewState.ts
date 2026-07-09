import { useEffect, useMemo, useState } from "react";

import type { FilePreviewContentState } from "@delpi/plugin-ui";

import {
  fetchPlanEvidenceContent,
  fetchPlanEvidenceFileBlob,
} from "../../api/actionPlansApi";
import type { PlanEvidence } from "../../types/rnc8d";
import { resolveEvidencePreviewMode } from "./evidencePreviewUtils";

const EMPTY_TEXT_STATE: FilePreviewContentState = {
  kind: "text",
  loading: false,
  error: null,
  previewUrl: null,
  textContent: null,
  textTruncated: false,
  spreadsheetData: null,
  docxData: null,
};

export function usePlanEvidencePreviewState(planId: string, evidence: PlanEvidence | null) {
  const mode = evidence ? resolveEvidencePreviewMode(evidence) : "none";

  const blobSource = useMemo(() => {
    if (!evidence || mode === "none" || mode === "text") return null;
    return () => fetchPlanEvidenceFileBlob(planId, evidence.id);
  }, [evidence, mode, planId]);

  const [textState, setTextState] = useState<FilePreviewContentState>({
    ...EMPTY_TEXT_STATE,
    kind: mode === "text" ? "text" : "none",
    loading: mode === "text",
  });

  useEffect(() => {
    if (!evidence || mode !== "text") {
      setTextState({ ...EMPTY_TEXT_STATE, kind: mode === "text" ? "text" : "none" });
      return;
    }

    let cancelled = false;
    setTextState((current) => ({ ...current, kind: "text", loading: true, error: null }));

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
  }, [evidence, mode, planId]);

  return {
    mode,
    blobSource,
    previewState: mode === "text" ? textState : undefined,
  };
}
