import { useEffect, useState } from "react";

export type RequestProgress = {
  completed: number;
  total: number;
};

export const EMPTY_REQUEST_PROGRESS: RequestProgress = { completed: 0, total: 0 };

export function getLoadingPercent(active: boolean, progress: RequestProgress): number {
  if (!active || progress.total <= 0) return 0;
  return Math.min(100, Math.round((progress.completed / progress.total) * 100));
}

export function useLoadingProgress(active: boolean, progress: RequestProgress): number {
  return getLoadingPercent(active, progress);
}

export function beginSingleRequestProgress(
  onProgress: (progress: RequestProgress) => void,
): void {
  onProgress({ completed: 0, total: 1 });
}

export function finishSingleRequestProgress(
  onProgress: (progress: RequestProgress) => void,
  aborted: boolean,
): void {
  if (!aborted) {
    onProgress({ completed: 1, total: 1 });
  }
}

export function useTrackedSingleFetchProgress(fetching: boolean): RequestProgress {
  const [progress, setProgress] = useState<RequestProgress>(EMPTY_REQUEST_PROGRESS);

  useEffect(() => {
    if (fetching) {
      beginSingleRequestProgress(setProgress);
      return;
    }
    finishSingleRequestProgress(setProgress, false);
  }, [fetching]);

  return progress;
}
