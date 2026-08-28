import { useCallback, useEffect, useState } from "react";

import { fetchOverview } from "../api/ppcApi";
import type { OverviewPayload, PpcBranch, VolumeView } from "../types";

export function useOverview(
  branch: PpcBranch,
  volumeView: VolumeView = "day",
  startDate: string | null = null,
  endDate: string | null = null,
) {
  const [data, setData] = useState<OverviewPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchOverview({
      branch,
      volumeView,
      startDate,
      endDate,
      signal: controller.signal,
    })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar o painel.");
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, endDate, reloadToken, startDate, volumeView]);

  return { data, loading, error, reload };
}
