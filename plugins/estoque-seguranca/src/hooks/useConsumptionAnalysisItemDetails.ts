import { useCallback, useEffect, useRef, useState } from "react";

import { fetchConsumptionAnalysisItemDetails } from "../api/safetyStockApi";
import type { SectionErrorState } from "../types/api";
import { toSectionError } from "../types/api";
import type { ConsumptionAnalysisItemDetails } from "../types/consumptionAnalysis";

export function useConsumptionAnalysisItemDetails(
  branch: string | null,
  productCode: string | null,
) {
  const [data, setData] = useState<ConsumptionAnalysisItemDetails | null>(null);
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

    const requestBranch = branch;
    const requestProductCode = productCode;
    const requestId = ++requestIdRef.current;
    const controller = new AbortController();

    async function run() {
      try {
        setError(null);
        setLoading(true);
        const result = await fetchConsumptionAnalysisItemDetails(
          requestBranch,
          requestProductCode,
          { signal: controller.signal },
        );
        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setData(result);
      } catch (reason) {
        if (controller.signal.aborted || requestId !== requestIdRef.current) return;
        setError(toSectionError(reason));
        setData(null);
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
