import { useCallback, useEffect, useState } from "react";

import { fetchReportsCatalog } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { PpcBranch, ReportsCatalogPayload } from "../types";

export function useReportsCatalog(branch: PpcBranch) {
  const [data, setData] = useState<ReportsCatalogPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchReportsCatalog({ branch, signal: controller.signal })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.reports.loadError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, reloadToken]);

  return { data, loading, error, reload };
}
