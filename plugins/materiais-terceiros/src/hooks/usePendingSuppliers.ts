import { useCallback, useEffect, useRef, useState } from "react";

import { fetchPendingSuppliers } from "../api/thirdPartyMaterialsApi";
import { toSectionError, type SectionErrorState } from "../types/api";
import type { PendingSupplierPage, ThirdPartyMaterialsQuery } from "../types/thirdPartyMaterials";

export function usePendingSuppliers(
  query: ThirdPartyMaterialsQuery | null,
  page: number,
  pageSize: number,
) {
  const [data, setData] = useState<PendingSupplierPage | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<SectionErrorState | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const requestIdRef = useRef(0);
  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  useEffect(() => {
    const requestId = ++requestIdRef.current;
    if (!query) {
      setData(null);
      setError(null);
      setLoading(false);
      setRefreshing(false);
      return;
    }
    const controller = new AbortController();
    const hasPreviousData = data !== null;
    async function run() {
      setError(null);
      if (hasPreviousData) setRefreshing(true);
      else setLoading(true);
      try {
        const result = await fetchPendingSuppliers(query!, page, pageSize, {
          signal: controller.signal,
        });
        if (!controller.signal.aborted && requestId === requestIdRef.current) {
          setData(result);
        }
      } catch (reason) {
        if (!controller.signal.aborted && requestId === requestIdRef.current) {
          setError(toSectionError(reason));
        }
      } finally {
        if (!controller.signal.aborted && requestId === requestIdRef.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }
    void run();
    return () => controller.abort();
    // Previous data is a loading state indicator, not a fetch dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, page, pageSize, reloadKey]);

  return { data, loading, refreshing, error, reload };
}
