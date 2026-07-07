import { useEffect, useState } from "react";

import {
  fetchDepartmentIdd,
  type DepartmentIddItem,
} from "../api/departmentIddApi";
import {
  resolveSiBranchFilter,
  type DepartmentIddFilterInput,
} from "../utils/departmentIddFilters";

export type UseDepartmentIddResult = {
  item: DepartmentIddItem | null;
  loading: boolean;
  error: string | null;
};

export function useDepartmentIdd(
  departmentId: string,
  filters: DepartmentIddFilterInput
): UseDepartmentIddResult {
  const [item, setItem] = useState<DepartmentIddItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { competence, dateStart, dateEnd, branches } = filters;
  const branch = resolveSiBranchFilter(branches);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setItem(null);
      setLoading(true);
      setError(null);

      try {
        const result = await fetchDepartmentIdd({
          departmentId,
          competence: competence || undefined,
          startDate: dateStart || undefined,
          endDate: dateEnd || undefined,
          branch,
          signal: controller.signal,
        });
        setItem(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        setItem(null);
        setError(err instanceof Error ? err.message : "Falha ao carregar IDD");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => controller.abort();
  }, [departmentId, competence, dateStart, dateEnd, branch]);

  return { item, loading, error };
}

export function formatDepartmentIddScore(score?: number | null): string | null {
  if (score == null || Number.isNaN(score)) {
    return null;
  }
  return score.toFixed(1);
}
