import { useEffect, useState } from "react";

import {
  fetchPerBranchMetricSlices,
  type DashboardGoalFields,
  type PerBranchMetricSlices,
} from "../utils/goalDisplay";

export function usePerBranchIddSlices<T extends DashboardGoalFields>(
  enabled: boolean,
  fetchMetric: (
    branch: "01" | "02",
    signal?: AbortSignal,
  ) => Promise<T>,
  getRealized: (data: T) => number | null | undefined,
  deps: readonly unknown[],
): PerBranchMetricSlices<T> | null {
  const [branches, setBranches] = useState<PerBranchMetricSlices<T> | null>(null);

  useEffect(() => {
    if (!enabled) {
      setBranches(null);
      return;
    }

    const controller = new AbortController();

    void fetchPerBranchMetricSlices(fetchMetric, getRealized, controller.signal).then(
      (next) => {
        if (!controller.signal.aborted) {
          setBranches(next);
        }
      },
    );

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ...deps]);

  return branches;
}
