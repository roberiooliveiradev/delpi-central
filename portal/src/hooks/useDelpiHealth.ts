// src/hooks/useDelpiHealth.ts

import { useEffect, useState, useCallback, useRef } from "react";
import { useDelpiApi } from "./useDelpiApi";
import type { HealthStatus } from "../data/delpiApi";

interface UseDelpiHealthOptions {
  pollingInterval?: number; // em ms (ex: 10000)
}

export const useDelpiHealth = (
  options?: UseDelpiHealthOptions
) => {
  const api = useDelpiApi();
  const pollingInterval = options?.pollingInterval;

  const [data, setData] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const mountedRef = useRef(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchHealth = useCallback(async () => {
    if (!api) return;

    try {
      setError(null);
      const res = await api.getHealth();

      if (!mountedRef.current) return;

      setData(res);
      setLastChecked(new Date());
    } catch (err: any) {
      if (!mountedRef.current) return;
      setError(err?.message ?? "Falha ao consultar health");
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    mountedRef.current = true;

    if (!api) return;

    setLoading(true);
    fetchHealth();

    if (pollingInterval) {
      intervalRef.current = setInterval(
        fetchHealth,
        pollingInterval
      );
    }

    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [api, pollingInterval, fetchHealth]);

  const reload = useCallback(() => {
    setLoading(true);
    fetchHealth();
  }, [fetchHealth]);

  return {
    data,
    loading,
    error,
    lastChecked,
    reload,
  };
};