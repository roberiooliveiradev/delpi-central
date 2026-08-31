import { useEffect, useMemo, useState } from "react";

import {
  fetchDepartmentIndicators,
  type DepartmentIndicatorsItem,
} from "../../api/analyticsApi";
import {
  resolveSiBranchFilter,
  type DepartmentIddFilterInput,
} from "./departmentIddFilters";
import { buildSiIndicatorScoreMap } from "./goalDisplay";

export type UseDepartmentIndicatorScoresResult = {
  item: DepartmentIndicatorsItem | null;
  scoresById: Record<string, number | null>;
  loading: boolean;
  error: string | null;
};

const sessionCache = new Map<string, DepartmentIndicatorsItem | null>();

function cacheKey(
  departmentId: string,
  competence: string,
  dateStart: string,
  dateEnd: string,
  branch: string | undefined,
): string {
  return [departmentId, competence, dateStart, dateEnd, branch ?? ""].join("|");
}

export function useDepartmentIndicatorScores(
  departmentId: string,
  filters: DepartmentIddFilterInput,
): UseDepartmentIndicatorScoresResult {
  const [item, setItem] = useState<DepartmentIndicatorsItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { competence, dateStart, dateEnd, branches } = filters;
  const branch = resolveSiBranchFilter(branches);
  const key = cacheKey(departmentId, competence, dateStart, dateEnd, branch);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      if (sessionCache.has(key)) {
        setItem(sessionCache.get(key) ?? null);
        setLoading(false);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const result = await fetchDepartmentIndicators({
          departmentId,
          competence: competence || undefined,
          startDate: dateStart || undefined,
          endDate: dateEnd || undefined,
          branch,
          signal: controller.signal,
        });
        sessionCache.set(key, result);
        setItem(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        setItem(null);
        setError(
          err instanceof Error
            ? err.message
            : "Falha ao carregar indicadores do SI",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => controller.abort();
  }, [departmentId, competence, dateStart, dateEnd, branch, key]);

  const scoresById = useMemo(
    () => buildSiIndicatorScoreMap(item?.indicators),
    [item],
  );

  return { item, scoresById, loading, error };
}
