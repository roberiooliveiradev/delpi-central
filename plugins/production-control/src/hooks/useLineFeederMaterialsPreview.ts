import { useCallback, useEffect, useRef, useState } from "react";

import { httpErrorStatus } from "../api/httpClient";
import { previewLineFeederMaterials } from "../api/ppcApi";
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
 * Prévia E3 sob demanda — sem cache de coletas anteriores e sem auto-fetch.
 * Descarta respostas que não correspondem à solicitação vigente (filial/CTs/horas).
 */
export function useLineFeederMaterialsPreview(branch: PpcBranch) {
  const [data, setData] = useState<LineFeederMaterialsPreviewPayload | null>(null);
  const [query, setQuery] = useState<LineFeederCollectQuery | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<LineFeederMaterialsError | null>(null);
  const requestSeq = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  const clear = useCallback(() => {
    requestSeq.current += 1;
    abortRef.current?.abort();
    abortRef.current = null;
    setData(null);
    setQuery(null);
    setError(null);
    setLoading(false);
  }, []);

  const run = useCallback(
    async (next: LineFeederCollectQuery) => {
      const seq = ++requestSeq.current;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setQuery(next);
      setLoading(true);
      setError(null);
      try {
        const payload = await previewLineFeederMaterials({
          branch,
          workCenters: next.workCenters,
          hoursPerWorkCenter: next.hoursPerWorkCenter,
          signal: controller.signal,
        });
        if (seq !== requestSeq.current) return;
        setData(payload);
        setError(null);
      } catch (err: unknown) {
        if (controller.signal.aborted || seq !== requestSeq.current) return;
        setData(null);
        setError(mapError(err));
      } finally {
        if (seq === requestSeq.current) setLoading(false);
      }
    },
    [branch],
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
    run,
    reload,
    clear,
    hasQuery: query !== null,
  };
}
