import { useCallback, useEffect, useRef, useState } from "react";

import { fetchSummary } from "../api/thirdPartyMaterialsApi";
import type { SectionErrorState } from "../types/api";
import { toSectionError } from "../types/api";
import type { SummaryData, ThirdPartyMaterialsQuery } from "../types/thirdPartyMaterials";

export function useSummary(query: ThirdPartyMaterialsQuery | null) {
  const [data, setData] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<SectionErrorState | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const requestIdRef = useRef(0);
  const hasLoadedOnceRef = useRef(false);

  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  useEffect(() => {
    if (!query) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    const requestId = ++requestIdRef.current;
    const controller = new AbortController();
    const params = query;

    async function run() {
      try {
        setError(null);
        if (hasLoadedOnceRef.current) setRefreshing(true);
        else setLoading(true);

        const result = await fetchSummary(params, { signal: controller.signal });
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
  }, [query, reloadKey]);

  return { data, loading, refreshing, error, reload };
}
