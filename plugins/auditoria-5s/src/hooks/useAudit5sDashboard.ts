import { useCallback, useEffect, useState } from "react";

import { fetchAudit5sDashboard } from "../api/audit5sApi";
import type { AuditDashboardData, AuditDashboardFilterParams } from "../types/auditDashboard";

export function useAudit5sDashboard(apiParams: AuditDashboardFilterParams) {
  const [data, setData] = useState<AuditDashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchAudit5sDashboard(apiParams);
        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Erro ao carregar dashboard.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [apiParams, reloadKey]);

  return {
    data,
    loading,
    error,
    reload,
    isRefreshing: loading && Boolean(data),
  };
}
