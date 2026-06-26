import { useEffect, useMemo, useState } from "react";

import { getHrBranches, getHrSnapshot } from "../api/hrApi";
import type { HrFilterParams } from "../types/hr";
import type { RequestProgress } from "../utils/loadingProgress";
import type { HrBranchGoalSnapshots } from "../utils/hrBranchIdd";
import { useHrResource } from "./useHrResource";

export function useHrDashboard(apiParams: HrFilterParams) {
  const [branchGoalSnapshots, setBranchGoalSnapshots] =
    useState<HrBranchGoalSnapshots | null>(null);

  const snapshotResource = useHrResource(
    (signal) => getHrSnapshot(apiParams, signal),
    [apiParams.branch, apiParams.end_date, apiParams.start_date]
  );

  useEffect(() => {
    if (apiParams.branch) {
      setBranchGoalSnapshots(null);
      return;
    }

    const controller = new AbortController();

    void Promise.allSettled([
      getHrSnapshot({ ...apiParams, branch: "01" }, controller.signal),
      getHrSnapshot({ ...apiParams, branch: "02" }, controller.signal),
    ]).then((results) => {
      if (controller.signal.aborted) return;
      setBranchGoalSnapshots({
        filial01: results[0].status === "fulfilled" ? results[0].value : null,
        filial02: results[1].status === "fulfilled" ? results[1].value : null,
      });
    });

    return () => controller.abort();
  }, [apiParams.branch, apiParams.end_date, apiParams.start_date]);

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
    branchGoalSnapshots,
    branchOptions,
    loading,
    refreshing,
    requestProgress,
    error,
    reload,
  };
}
