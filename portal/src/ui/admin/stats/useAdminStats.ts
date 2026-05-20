// src/ui/admin/stats/useAdminStats.ts

import { useCallback, useContext, useEffect, useMemo, useState } from "react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi, type AdminStatistics } from "../../../data/adminApi";
import type { ChartSegment } from "./StatsCharts";
import { STATS_CHART_COLORS } from "./statsTheme";

export type StatsChartsData = {
  userSegments: ChartSegment[];
  appSegments: ChartSegment[];
  notificationSegments: ChartSegment[];
};

export function useAdminStats() {
  const { getAccessToken } = useContext(AuthContext);
  const [stats, setStats] = useState<AdminStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const api = useMemo(() => {
    return new AdminApi(new ApiClient("", getAccessToken));
  }, [getAccessToken]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.getAdminStatistics();
      setStats(data);
    } catch (err) {
      setStats(null);
      setError(
        err instanceof Error ? err.message : "Falha ao carregar estatísticas",
      );
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  const charts = useMemo(() => {
    if (!stats) return null;

    const usage = stats.apps.usage;
    const ghostCount = usage?.ghostApps?.length ?? 0;
    const usedInPeriod = usage?.usedInPeriod ?? 0;
    const appsActive = stats.apps.active;
    const appsIdle = Math.max(0, appsActive - usedInPeriod);

    const userSegments: ChartSegment[] = [
      {
        label: "Ativos",
        value: stats.users.active,
        color: STATS_CHART_COLORS.success,
      },
      {
        label: "Inativos",
        value: stats.users.inactive,
        color: STATS_CHART_COLORS.muted,
      },
    ];

    const appSegments: ChartSegment[] = [
      {
        label: "Em uso agora",
        value: usage?.inUseNow ?? 0,
        color: STATS_CHART_COLORS.c1,
      },
      {
        label: "Usadas (30d)",
        value: Math.max(0, usedInPeriod - (usage?.inUseNow ?? 0)),
        color: STATS_CHART_COLORS.c3,
      },
      {
        label: "Fantasmas",
        value: ghostCount,
        color: STATS_CHART_COLORS.c5,
      },
      {
        label: "Sem uso recente",
        value: appsIdle,
        color: STATS_CHART_COLORS.muted,
      },
    ];

    const notifyTotal = stats.notifications?.dispatchesTotal ?? 0;
    const notifyPending = stats.notifications?.dispatchesPending ?? 0;
    const notifyCompleted = stats.notifications?.dispatchesCompleted ?? 0;
    const notifyFailed = stats.notifications?.dispatchesFailed ?? 0;
    const notifyOther = Math.max(
      0,
      notifyTotal - notifyPending - notifyCompleted - notifyFailed,
    );

    const notificationSegments: ChartSegment[] = [
      {
        label: "Concluídos",
        value: notifyCompleted,
        color: STATS_CHART_COLORS.success,
      },
      {
        label: "Pendentes",
        value: notifyPending,
        color: STATS_CHART_COLORS.primary,
      },
      {
        label: "Falhas",
        value: notifyFailed,
        color: STATS_CHART_COLORS.danger,
      },
      {
        label: "Outros",
        value: notifyOther,
        color: STATS_CHART_COLORS.muted,
      },
    ];

    return { userSegments, appSegments, notificationSegments };
  }, [stats]);

  return { stats, loading, error, load, charts };
}
