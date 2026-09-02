import { useCallback, useMemo } from "react";

import {
  getUnproductiveHoursRanking,
  getUnproductiveHoursSummary,
} from "../api/unproductiveHoursApi";
import type {
  UnproductiveHoursQueryFilters,
  UnproductiveHoursRankingData,
  UnproductiveHoursSummaryData,
} from "../types/unproductiveHours";
import { UNPRODUCTIVE_HOURS_RANKING_LIMIT } from "../types/unproductiveHours";
import { useAsyncResource } from "./useAsyncResource";

export type UnproductiveHoursDashboardBundle = {
  summary: UnproductiveHoursSummaryData;
  byStopReason: UnproductiveHoursRankingData;
  byOperator: UnproductiveHoursRankingData;
  byResource: UnproductiveHoursRankingData;
};

export function useUnproductiveHoursDashboard(
  filters: UnproductiveHoursQueryFilters | null,
  enabled: boolean,
) {
  const filtersKey = useMemo(() => {
    if (!filters) return "";
    return [
      filters.branch,
      filters.start_date,
      filters.end_date,
      filters.stop_reason ?? "",
      filters.resource ?? "",
      filters.cost_center ?? "",
      filters.operator_code ?? "",
    ].join("|");
  }, [filters]);

  const fetcher = useCallback(
    async (signal: AbortSignal): Promise<UnproductiveHoursDashboardBundle> => {
      if (!filters) {
        throw new Error("Filtros de horas improdutivas inválidos.");
      }
      const base = { ...filters };
      const [summary, byStopReason, byOperator, byResource] = await Promise.all([
        getUnproductiveHoursSummary(base, { signal }),
        getUnproductiveHoursRanking(
          { ...base, rank_by: "stop_reason", limit: UNPRODUCTIVE_HOURS_RANKING_LIMIT },
          { signal },
        ),
        getUnproductiveHoursRanking(
          { ...base, rank_by: "operator", limit: UNPRODUCTIVE_HOURS_RANKING_LIMIT },
          { signal },
        ),
        getUnproductiveHoursRanking(
          { ...base, rank_by: "resource", limit: UNPRODUCTIVE_HOURS_RANKING_LIMIT },
          { signal },
        ),
      ]);
      return { summary, byStopReason, byOperator, byResource };
    },
    [filters],
  );

  return useAsyncResource(fetcher, [filtersKey], enabled && Boolean(filters));
}
