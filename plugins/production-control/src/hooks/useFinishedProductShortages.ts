import { useCallback, useEffect, useState } from "react";

import { fetchFinishedProductShortages } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { FinishedProductShortagePayload, MaterialsSetStatus, PpcBranch } from "../types";
import { canQueryFinishedProductShortages } from "../utils/finishedProductShortageQuery";

export function useFinishedProductShortages(
  branch: PpcBranch,
  product: string,
  status: MaterialsSetStatus,
) {
  const [data, setData] = useState<FinishedProductShortagePayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);
  const canFetch = canQueryFinishedProductShortages(product);

  useEffect(() => {
    if (!canFetch) {
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    fetchFinishedProductShortages({
      branch,
      product: product.trim(),
      status,
      refresh: reloadToken > 0,
      signal: controller.signal,
    })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.materials.paShortage.loadError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, canFetch, product, reloadToken, status]);

  return {
    data,
    loading: loading && data === null,
    refreshing: loading && data !== null,
    error,
    reload,
    canFetch,
  };
}
