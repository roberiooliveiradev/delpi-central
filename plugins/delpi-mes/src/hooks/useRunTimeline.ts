import { useEffect, useState } from "react";
import { getRunTimeline } from "../api/mesApi";
import type { RunTimeline } from "../types/mes";

export function useRunTimeline(runId: string | null, signature: string | null, enabled: boolean) {
  const [data, setData] = useState<RunTimeline | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    queueMicrotask(() => { setData(null); setError(null); });
    if (!runId || !enabled) return;
    const controller = new AbortController();
    queueMicrotask(() => setLoading(true));
    getRunTimeline(runId, controller.signal)
      .then(setData)
      .catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Falha ao carregar a timeline."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [runId, signature, enabled]);
  return { data, error, loading };
}
