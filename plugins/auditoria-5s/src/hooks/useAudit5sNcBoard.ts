import { useCallback, useEffect, useState } from "react";

import { fetchNcBoard } from "../api/audit5sApi";
import type { NcBoardData, NcBoardFilterParams } from "../types/ncManagement";

const POLL_INTERVAL_MS = 30_000;

export function useAudit5sNcBoard(apiParams: NcBoardFilterParams) {
  const [data, setData] = useState<NcBoardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<number | null>(null);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchNcBoard(apiParams);
        if (!cancelled) {
          setData(result);
          setLastUpdatedAt(Date.now());
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Erro ao carregar não conformidades.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [apiParams, reloadKey]);

  return {
    data,
    loading,
    error,
    reload,
    lastUpdatedAt,
    isRefreshing: loading && Boolean(data),
  };
}
