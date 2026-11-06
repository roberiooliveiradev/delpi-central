import { useCallback, useEffect, useRef, useState } from "react";

import { httpErrorStatus } from "../api/httpClient";
import { previewLineFeederMaterialsStream } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { LineFeederMaterialsPreviewPayload, PpcBranch } from "../types";

export type LineFeederCollectQuery = {
  workCenters: string[];
  hoursPerWorkCenter: number;
};

export type LineFeederMaterialsErrorKind =
  | "forbidden"
  | "not_found"
  | "stale"
  | "validation"
  | "gateway"
  | "generic";

export type LineFeederMaterialsError = {
  kind: LineFeederMaterialsErrorKind;
  message: string;
};

export type LineFeederProgressLog = {
  id: string;
  message: string;
  percent: number;
  step: string;
};

const MAX_PROGRESS_LOGS = 14;

function mapError(err: unknown): LineFeederMaterialsError {
  const status = httpErrorStatus(err);
  const fallback = copy.lineFeeder.materialsPreview.loadError;
  const message = err instanceof Error && err.message.trim() ? err.message : fallback;
  if (status === 403) return { kind: "forbidden", message };
  if (status === 404) return { kind: "not_found", message };
  if (status === 409) {
    return {
      kind: "stale",
      message: copy.lineFeeder.materialsPreview.staleError,
    };
  }
  if (status === 422) return { kind: "validation", message };
  if (status === 502) return { kind: "gateway", message };
  return { kind: "generic", message };
}

/**
 * Prévia E3 sob demanda — stream SSE com progresso real.
 * Descarta respostas que não correspondem à solicitação vigente (filial/CTs/horas).
 */
export function useLineFeederMaterialsPreview(branch: PpcBranch) {
  const [data, setData] = useState<LineFeederMaterialsPreviewPayload | null>(null);
  const [query, setQuery] = useState<LineFeederCollectQuery | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<LineFeederMaterialsError | null>(null);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressLogs, setProgressLogs] = useState<LineFeederProgressLog[]>([]);
  const requestSeq = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const logSeq = useRef(0);

  const resetProgress = useCallback(() => {
    setProgressPercent(0);
    setProgressLogs([]);
  }, []);

  const clear = useCallback(() => {
    requestSeq.current += 1;
    abortRef.current?.abort();
    abortRef.current = null;
    setData(null);
    setQuery(null);
    setError(null);
    setLoading(false);
    resetProgress();
  }, [resetProgress]);

  const run = useCallback(
    async (next: LineFeederCollectQuery) => {
      const seq = ++requestSeq.current;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setQuery(next);
      setLoading(true);
      setError(null);
      resetProgress();
      try {
        const payload = await previewLineFeederMaterialsStream({
          branch,
          workCenters: next.workCenters,
          hoursPerWorkCenter: next.hoursPerWorkCenter,
          signal: controller.signal,
          onProgress: (event) => {
            if (seq !== requestSeq.current) return;
            const percent = Math.max(0, Math.min(100, Number(event.percent) || 0));
            setProgressPercent((prev) => Math.max(prev, percent));
            const message = String(event.message || "").trim();
            if (!message) return;
            const id = `p-${++logSeq.current}`;
            setProgressLogs((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.message === message && last.step === event.step) {
                return prev.map((entry, index) =>
                  index === prev.length - 1
                    ? { ...entry, percent, id }
                    : entry,
                );
              }
              return [
                ...prev,
                {
                  id,
                  message,
                  percent,
                  step: String(event.step || ""),
                },
              ].slice(-MAX_PROGRESS_LOGS);
            });
          },
        });
        if (seq !== requestSeq.current) return;
        setData(payload);
        setError(null);
        setProgressPercent(100);
      } catch (err: unknown) {
        if (controller.signal.aborted || seq !== requestSeq.current) return;
        setData(null);
        setError(mapError(err));
      } finally {
        if (seq === requestSeq.current) {
          setLoading(false);
          if (seq === requestSeq.current && !controller.signal.aborted) {
            // Mantém o último percent/logs só até a próxima run/clear.
          }
        }
      }
    },
    [branch, resetProgress],
  );

  const reload = useCallback(() => {
    if (!query) return;
    void run(query);
  }, [query, run]);

  useEffect(() => {
    // Troca de filial invalida a fotografia anterior.
    clear();
  }, [branch, clear]);

  useEffect(
    () => () => {
      abortRef.current?.abort();
    },
    [],
  );

  return {
    data,
    query,
    loading,
    error,
    progressPercent,
    progressLogs,
    run,
    reload,
    clear,
    hasQuery: query !== null,
  };
}
