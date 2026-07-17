import { useCallback, useEffect, useRef, useState } from "react";

import { bootstrapSafetyStockFilters, fetchSafetyStockFilters } from "../api/safetyStockApi";
import type { SectionErrorState } from "../types/api";
import { toSectionError } from "../types/api";
import type { SafetyStockFiltersData } from "../types/safetyStock";

export function useSafetyStockFilters(branch: string, includeBlocked: boolean) {
  const [data, setData] = useState<SafetyStockFiltersData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<SectionErrorState | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const requestIdRef = useRef(0);

  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  useEffect(() => {
    const requestId = ++requestIdRef.current;
    const controller = new AbortController();

    async function run() {
      try {
        setLoading(true);
        setError(null);

        const result = branch
          ? await fetchSafetyStockFilters(branch, includeBlocked, { signal: controller.signal })
          : await bootstrapSafetyStockFilters(includeBlocked, { signal: controller.signal });

        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setData(result);
      } catch (reason) {
        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setError(toSectionError(reason));
      } finally {
        if (!controller.signal.aborted && requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [branch, includeBlocked, reloadKey]);

  return { data, loading, error, reload };
}
