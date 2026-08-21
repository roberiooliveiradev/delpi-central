import { useEffect, useMemo, useState } from "react";

export type RequestProgress = {
  completed: number;
  total: number;
};

const EMPTY_REQUEST_PROGRESS: RequestProgress = { completed: 0, total: 0 };

export function useLoadingProgress(active: boolean, progress: RequestProgress): number {
  return useMemo(() => {
    if (!active || progress.total <= 0) return 0;
    return Math.min(100, Math.round((progress.completed / progress.total) * 100));
  }, [active, progress.completed, progress.total]);
}

/** Progresso de uma requisição única: 0% enquanto busca, 100% ao concluir. */
export function useTrackedSingleFetchProgress(fetching: boolean): RequestProgress {
  const [progress, setProgress] = useState<RequestProgress>(EMPTY_REQUEST_PROGRESS);

  useEffect(() => {
    setProgress(fetching ? { completed: 0, total: 1 } : { completed: 1, total: 1 });
  }, [fetching]);

  return progress;
}
