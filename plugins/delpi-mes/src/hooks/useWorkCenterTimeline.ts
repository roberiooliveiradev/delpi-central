import { useEffect, useState } from "react";
import { getWorkCenterTimeline } from "../api/mesApi";
import type { BranchCode } from "../constants/routes";
import type { WorkCenterTimelineResponse } from "../types/mes";
import { dayRangeIso } from "../utils/dayTimeline";

export function useWorkCenterTimeline(branch: BranchCode, workCenter: string | null, signature: string | null, enabled: boolean, dayKey?: string | null) {
  const [data, setData] = useState<WorkCenterTimelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    queueMicrotask(() => { setData(null); setError(null); });
    if (!workCenter || !enabled) return;
    const controller = new AbortController();
    queueMicrotask(() => setLoading(true));
    getWorkCenterTimeline(branch, workCenter, dayRangeIso(dayKey), controller.signal)
      .then(setData)
      .catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Falha ao carregar o histórico do dia."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [branch, workCenter, signature, enabled, dayKey, reloadKey]);

  return { data, error, loading, retry: () => setReloadKey((key) => key + 1) };
}
