import { useMemo } from "react";

import { getHrBranches, getHrSnapshot } from "../api/hrApi";
import type { HrFilterParams } from "../types/hr";
import type { RequestProgress } from "../utils/loadingProgress";
import { useHrResource } from "./useHrResource";

export function useHrDashboard(apiParams: HrFilterParams) {
  const snapshotResource = useHrResource(
    (signal) => getHrSnapshot(apiParams, signal),
    [apiParams.branch, apiParams.end_date, apiParams.start_date]
  );

  const branchesResource = useHrResource(
    (signal) => getHrBranches(signal),
    []
  );

  const branchOptions = useMemo(
    () => branchesResource.data?.branches ?? [],
    [branchesResource.data?.branches]
  );

  const error = snapshotResource.error ?? branchesResource.error;

  const loading = snapshotResource.loading || branchesResource.loading;
  const refreshing = snapshotResource.refreshing || branchesResource.refreshing;

  const requestProgress = useMemo<RequestProgress>(() => {
    const total =
      snapshotResource.requestProgress.total + branchesResource.requestProgress.total;
    const completed =
      (snapshotResource.loading ? 0 : snapshotResource.requestProgress.completed) +
      (branchesResource.loading ? 0 : branchesResource.requestProgress.completed);
    return { completed, total: total || 2 };
  }, [
    snapshotResource.loading,
    snapshotResource.requestProgress,
    branchesResource.loading,
    branchesResource.requestProgress,
  ]);

  const reload = () => {
    snapshotResource.reload();
    branchesResource.reload();
  };

  return {
    snapshot: snapshotResource.data,
    branchOptions,
    loading,
    refreshing,
    requestProgress,
    error,
    reload,
  };
}
