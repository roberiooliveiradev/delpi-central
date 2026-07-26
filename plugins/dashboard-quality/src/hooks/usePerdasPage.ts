import { useCallback, useEffect, useState } from "react";

import { getReworkCostPct, getScrapCostPct } from "../api/qualityApi";
import type { CostPctSummary } from "../types/losses";
import { formatQualityApiError } from "../utils/formatQualityApiError";
import {
  fetchPerBranchMetricSlices,
  type PerBranchMetricSlices,
} from "../utils/goalDisplay";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

export type PerdasFilters = {
  branch?: string;
  start_date?: string;
  end_date?: string;
};

type UsePerdasPageResult = {
  scrap: CostPctSummary | null;
  rework: CostPctSummary | null;
  scrapBranches: PerBranchMetricSlices<CostPctSummary> | null;
  reworkBranches: PerBranchMetricSlices<CostPctSummary> | null;
  loading: boolean;
  refreshing: boolean;
  requestProgress: RequestProgress;
  error: string | null;
  reload: () => void;
};

export function usePerdasPage(filters: PerdasFilters): UsePerdasPageResult {
  const [scrap, setScrap] = useState<CostPctSummary | null>(null);
  const [rework, setRework] = useState<CostPctSummary | null>(null);
  const [scrapBranches, setScrapBranches] =
    useState<PerBranchMetricSlices<CostPctSummary> | null>(null);
  const [reworkBranches, setReworkBranches] =
    useState<PerBranchMetricSlices<CostPctSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [requestProgress, setRequestProgress] =
    useState<RequestProgress>(EMPTY_REQUEST_PROGRESS);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function load() {
      const hasData = scrap !== null || rework !== null;
      if (hasData) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      setRequestProgress(EMPTY_REQUEST_PROGRESS);

      const consolidated = !filters.branch;
      const baseParams = {
        branch: filters.branch,
        start_date: filters.start_date,
        end_date: filters.end_date,
      };

      try {
        type RunnerResult =
          | CostPctSummary
          | PerBranchMetricSlices<CostPctSummary>;

        const runners: Array<(signal: AbortSignal) => Promise<RunnerResult>> = [
          (signal) => getScrapCostPct(baseParams, signal),
          (signal) => getReworkCostPct(baseParams, signal),
        ];

        if (consolidated) {
          runners.push(
            (signal) =>
              fetchPerBranchMetricSlices(
                (branch, branchSignal) =>
                  getScrapCostPct(
                    { ...baseParams, branch },
                    branchSignal ?? signal,
                  ),
                (data) => data.scrap_cost_pct ?? null,
                signal,
              ),
            (signal) =>
              fetchPerBranchMetricSlices(
                (branch, branchSignal) =>
                  getReworkCostPct(
                    { ...baseParams, branch },
                    branchSignal ?? signal,
                  ),
                (data) => data.rework_cost_pct ?? null,
                signal,
              ),
          );
        }

        const results = await runParallelWithProgress(
          runners,
          controller.signal,
          setRequestProgress,
        );

        if (cancelled || controller.signal.aborted) return;

        const scrapResult = results[0];
        const reworkResult = results[1];

        if (scrapResult.status === "fulfilled") {
          setScrap(scrapResult.value as CostPctSummary);
        } else {
          setScrap(null);
        }
        if (reworkResult.status === "fulfilled") {
          setRework(reworkResult.value as CostPctSummary);
        } else {
          setRework(null);
        }

        if (consolidated && results.length >= 4) {
          const scrapBranchResult = results[2];
          const reworkBranchResult = results[3];
          setScrapBranches(
            scrapBranchResult.status === "fulfilled"
              ? (scrapBranchResult.value as PerBranchMetricSlices<CostPctSummary>)
              : null,
          );
          setReworkBranches(
            reworkBranchResult.status === "fulfilled"
              ? (reworkBranchResult.value as PerBranchMetricSlices<CostPctSummary>)
              : null,
          );
        } else {
          setScrapBranches(null);
          setReworkBranches(null);
        }

        if (
          scrapResult.status === "rejected" &&
          reworkResult.status === "rejected"
        ) {
          setError(
            formatQualityApiError(scrapResult.reason) ||
              "Não foi possível carregar os indicadores de perdas.",
          );
        }
      } catch (err) {
        if (cancelled || controller.signal.aborted) return;
        setError(
          formatQualityApiError(err) ||
            "Não foi possível carregar os indicadores de perdas.",
        );
      } finally {
        if (!cancelled && !controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- scrap/rework omitidos de propósito (evita loop)
  }, [
    filters.branch,
    filters.start_date,
    filters.end_date,
    reloadToken,
  ]);

  return {
    scrap,
    rework,
    scrapBranches,
    reworkBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    reload,
  };
}
