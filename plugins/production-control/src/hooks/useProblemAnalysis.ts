import { useCallback, useEffect, useState } from "react";

import { fetchProblemAnalysis } from "../api/ppcApi";
import type { PpcBranch, ProblemAnalysisPayload } from "../types";

export function useProblemAnalysis(branch: PpcBranch, issueId: string | null) {
  const [data, setData] = useState<ProblemAnalysisPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchProblemAnalysis({ branch, issueId, signal: controller.signal })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar análise.");
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, issueId, reloadToken]);

  return { data, loading, error, reload };
}
