import { useCallback, useEffect, useState } from "react";

import { fetchLineFeederRequirements } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { LineFeederRequirementsPayload, PpcBranch } from "../types";

export type LineFeederFilters = {
  cutoffDate: string;
  cutoffTime: string;
  workCenter: string;
  status: string;
};

/** Hoje às 12:00 — o corte mais pedido é «o que precisa estar lá antes do almoço». */
export function defaultLineFeederFilters(): LineFeederFilters {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return {
    cutoffDate: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
    cutoffTime: "12:00",
    workCenter: "",
    status: "",
  };
}

export function useLineFeeder(branch: PpcBranch, filters: LineFeederFilters) {
  const [data, setData] = useState<LineFeederRequirementsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    if (!filters.cutoffDate) return;
    const controller = new AbortController();
    setLoading(true);
    fetchLineFeederRequirements({
      branch,
      cutoffDate: filters.cutoffDate,
      cutoffTime: filters.cutoffTime || null,
      workCenter: filters.workCenter || null,
      status: filters.status || null,
      refresh: reloadToken > 0,
      signal: controller.signal,
    })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.lineFeeder.loadError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    branch,
    filters.cutoffDate,
    filters.cutoffTime,
    filters.status,
    filters.workCenter,
    reloadToken,
  ]);

  return {
    data,
    loading: loading && data === null,
    refreshing: loading && data !== null,
    error,
    reload,
  };
}
