import { useCallback, useEffect, useRef, useState } from "react";

import { fetchSafetyStockSummary } from "../api/safetyStockApi";
import type { SectionErrorState } from "../types/api";
import { toSectionError } from "../types/api";
import type { SafetyStockQueryParams, SafetyStockSummaryData } from "../types/safetyStock";

export function useSafetyStockSummary(appliedParams: SafetyStockQueryParams | null) {
  const [data, setData] = useState<SafetyStockSummaryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<SectionErrorState | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);

  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  useEffect(() => {
    if (!appliedParams?.branch) return;

    const requestId = ++requestIdRef.current;
    const controller = new AbortController();
    const params = appliedParams;

    async function run() {
      try {
        setError(null);
        if (hasLoadedOnceRef.current) setRefreshing(true);
        else setLoading(true);

        const result = await fetchSafetyStockSummary(params, { signal: controller.signal });
        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setData(result);
        hasLoadedOnceRef.current = true;
      } catch (reason) {
        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setError(toSectionError(reason));
      } finally {
        if (!controller.signal.aborted && requestId === requestIdRef.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [appliedParams, reloadKey]);

  return { data, loading, refreshing, error, reload };
}
