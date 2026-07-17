import { useCallback, useEffect, useRef, useState } from "react";

import { fetchSafetyStockItems } from "../api/safetyStockApi";
import type { SectionErrorState } from "../types/api";
import { toSectionError } from "../types/api";
import type { SafetyStockItemsData, SafetyStockQueryParams } from "../types/safetyStock";

export function useSafetyStockItems(
  appliedParams: SafetyStockQueryParams | null,
  page: number,
  pageSize: number,
) {
  const [data, setData] = useState<SafetyStockItemsData | null>(null);
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

        const result = await fetchSafetyStockItems(params, page, pageSize, {
          signal: controller.signal,
        });
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
  }, [appliedParams, page, pageSize, reloadKey]);

  return { data, loading, refreshing, error, reload };
}
