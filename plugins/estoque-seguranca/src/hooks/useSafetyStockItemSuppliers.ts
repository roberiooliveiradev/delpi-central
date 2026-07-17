import { useCallback, useEffect, useRef, useState } from "react";

import { fetchSafetyStockItemSuppliers } from "../api/safetyStockApi";
import type { SectionErrorState } from "../types/api";
import { toSectionError } from "../types/api";
import type { SafetyStockLinkedSuppliersData } from "../types/safetyStock";

export function useSafetyStockItemSuppliers(
  branch: string | null,
  productCode: string | null,
) {
  const [data, setData] = useState<SafetyStockLinkedSuppliersData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<SectionErrorState | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const requestIdRef = useRef(0);

  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  useEffect(() => {
    if (!branch || !productCode) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }

    const resolvedBranch = branch;
    const resolvedProductCode = productCode;
    const requestId = ++requestIdRef.current;
    const controller = new AbortController();

    async function run() {
      try {
        setError(null);
        setLoading(true);
        const result = await fetchSafetyStockItemSuppliers(
          resolvedBranch,
          resolvedProductCode,
          {
            signal: controller.signal,
          },
        );
        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setData(result);
      } catch (reason) {
        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setData(null);
        setError(toSectionError(reason));
      } finally {
        if (!controller.signal.aborted && requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [branch, productCode, reloadKey]);

  return { data, loading, error, reload };
}
