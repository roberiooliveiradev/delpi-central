import { useCallback, useEffect, useRef, useState } from "react";
import { getMonitoring } from "../api/mesApi";
import { MONITORING_POLL_MS } from "../constants/monitoring";
import type { BranchCode } from "../constants/routes";
import type { MonitoringResponse } from "../types/mes";

export function useMonitoringData(branch: BranchCode) {
  const [data, setData] = useState<MonitoringResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const active = useRef(false);
  const hasData = useRef(false);

  const refresh = useCallback(async () => {
    if (active.current || document.hidden || !navigator.onLine) return;
    active.current = true;
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    setRefreshing(hasData.current);
    try {
      const response = await getMonitoring(branch, next.signal);
      setData(response);
      hasData.current = true;
      setError(null);
    } catch (reason) {
      if (!next.signal.aborted) setError(reason instanceof Error ? reason.message : "Falha ao atualizar o monitoramento.");
    } finally {
      if (!next.signal.aborted) { setLoading(false); setRefreshing(false); }
      active.current = false;
    }
  }, [branch]);

  useEffect(() => {
    hasData.current = false;
    queueMicrotask(() => { setData(null); setError(null); setLoading(true); });
    let timeout: number | undefined;
    let disposed = false;
    const cycle = async () => {
      await refresh();
      if (!disposed) timeout = window.setTimeout(cycle, MONITORING_POLL_MS);
    };
    const resume = () => { if (!document.hidden && navigator.onLine) void refresh(); };
    void cycle();
    document.addEventListener("visibilitychange", resume);
    window.addEventListener("online", resume);
    return () => {
      disposed = true;
      if (timeout) window.clearTimeout(timeout);
      controller.current?.abort();
      document.removeEventListener("visibilitychange", resume);
      window.removeEventListener("online", resume);
    };
  }, [branch, refresh]);

  return { data, error, loading, refreshing, refresh };
}
