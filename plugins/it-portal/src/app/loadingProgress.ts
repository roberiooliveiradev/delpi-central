/** Hooks de progresso injetados no DataTable kit (contrato `RequestProgress` do plugin-ui). */
import { useMemo } from "react";

type RequestProgress = { completed: number; total: number };

const FETCHING: RequestProgress = { completed: 0, total: 1 };
const SETTLED: RequestProgress = { completed: 1, total: 1 };

export function useLoadingProgress(active: boolean, progress: RequestProgress): number {
  return useMemo(() => {
    if (!active || progress.total <= 0) return 0;
    return Math.min(100, Math.round((progress.completed / progress.total) * 100));
  }, [active, progress.completed, progress.total]);
}

export function useTrackedSingleFetchProgress(fetching: boolean): RequestProgress {
  return fetching ? FETCHING : SETTLED;
}
