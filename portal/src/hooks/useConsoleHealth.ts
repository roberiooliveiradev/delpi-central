// src/hooks/useConsoleHealth.ts

import { useCallback, useEffect, useRef, useState } from "react";

import type { ConsoleHealthStatus } from "../data/delpiApi";
import { useDelpiApi } from "./useDelpiApi";
import { STATS_AUTO_REFRESH_MS } from "../ui/admin/stats/statsTheme";

export function useConsoleHealth() {
  const api = useDelpiApi();
  const [data, setData] = useState<ConsoleHealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const load = useCallback(
    async (options?: { silent?: boolean }) => {
      if (!api) return;

      if (!options?.silent) {
        setLoading(true);
      }
      setError(null);

      try {
        const payload = await api.getConsoleHealth();
        if (!mountedRef.current) return;
        setData(payload);
      } catch (err) {
        if (!mountedRef.current) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Falha ao carregar saúde do console");
      } finally {
        if (mountedRef.current && !options?.silent) {
          setLoading(false);
        }
      }
    },
    [api],
  );

  useEffect(() => {
    mountedRef.current = true;
    void load();

    const tick = () => {
      if (document.visibilityState !== "visible") return;
      void load({ silent: true });
    };

    const intervalId = window.setInterval(tick, STATS_AUTO_REFRESH_MS);
    document.addEventListener("visibilitychange", tick);

    return () => {
      mountedRef.current = false;
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [load]);

  return { data, loading, error, reload: () => void load() };
}
