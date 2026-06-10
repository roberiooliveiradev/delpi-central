import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type {
  PortalTourExplorersResponse,
  PortalTourTopExplorersResponse,
} from "../../../data/coreApi";
import { PORTAL_TOUR_VERSION } from "../../../tour/portalTourStorage";
import { STATS_AUTO_REFRESH_MS } from "./statsTheme";
import type { PortalTourStatusFilter } from "./portalTourAdminLabels";

const PAGE_SIZE = 20;

function normalizeTourAdminError(err: unknown): string {
  if (!(err instanceof Error)) {
    return "Falha ao carregar acompanhamento do tour.";
  }

  const message = err.message.trim();
  if (
    message.includes("<!doctype") ||
    message.includes("<html") ||
    message.includes("Internal Server Error")
  ) {
    return "Erro no servidor. Tente atualizar em instantes.";
  }

  return message.length > 280 ? `${message.slice(0, 277)}…` : message;
}

function settledValue<T>(result: PromiseSettledResult<T>): T | null {
  return result.status === "fulfilled" ? result.value : null;
}

function settledError(result: PromiseSettledResult<unknown>): string | null {
  return result.status === "rejected" ? normalizeTourAdminError(result.reason) : null;
}

export type PortalTourMonitoringSummary = {
  exploring: number;
  completed: number;
  dismissed: number;
  total: number;
};

export function usePortalTourAdminMonitoring() {
  const { getAccessToken, refreshToken } = useContext(AuthContext);
  const [statusFilter, setStatusFilter] = useState<PortalTourStatusFilter>("all");
  const [periodDays, setPeriodDays] = useState(7);
  const [page, setPage] = useState(0);
  const [listData, setListData] = useState<PortalTourExplorersResponse | null>(null);
  const [topData, setTopData] = useState<PortalTourTopExplorersResponse | null>(null);
  const [summary, setSummary] = useState<PortalTourMonitoringSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [topError, setTopError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);

  const adminApi = useMemo(
    () =>
      new AdminApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setListError(null);
    setTopError(null);

    try {
      const offset = page * PAGE_SIZE;
      const [
        exploringRes,
        completedRes,
        dismissedRes,
        allRes,
        listRes,
        topRes,
      ] = await Promise.allSettled([
        adminApi.listPortalTourExplorers({
          tourVersion: PORTAL_TOUR_VERSION,
          status: "exploring",
          limit: 1,
        }),
        adminApi.listPortalTourExplorers({
          tourVersion: PORTAL_TOUR_VERSION,
          status: "completed",
          limit: 1,
        }),
        adminApi.listPortalTourExplorers({
          tourVersion: PORTAL_TOUR_VERSION,
          status: "dismissed",
          limit: 1,
        }),
        adminApi.listPortalTourExplorers({
          tourVersion: PORTAL_TOUR_VERSION,
          status: "all",
          limit: 1,
        }),
        adminApi.listPortalTourExplorers({
          tourVersion: PORTAL_TOUR_VERSION,
          status: statusFilter === "all" ? "all" : statusFilter,
          limit: PAGE_SIZE,
          offset,
        }),
        adminApi.listPortalTourTopExplorers({
          tourVersion: PORTAL_TOUR_VERSION,
          periodDays,
          limit: 10,
        }),
      ]);

      const exploring = settledValue(exploringRes);
      const completed = settledValue(completedRes);
      const dismissed = settledValue(dismissedRes);
      const all = settledValue(allRes);
      const list = settledValue(listRes);
      const top = settledValue(topRes);

      setSummary({
        exploring: exploring?.total ?? 0,
        completed: completed?.total ?? 0,
        dismissed: dismissed?.total ?? 0,
        total: all?.total ?? 0,
      });
      setListData(list);
      setTopData(top);
      setListError(settledError(listRes));
      setTopError(settledError(topRes));
      setLastUpdatedAt(new Date().toISOString());
    } catch (err) {
      setListError(normalizeTourAdminError(err));
      setTopError(normalizeTourAdminError(err));
    } finally {
      setLoading(false);
    }
  }, [adminApi, page, periodDays, statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      void load();
    }, STATS_AUTO_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  useEffect(() => {
    setPage(0);
  }, [statusFilter]);

  const totalPages = listData
    ? Math.max(1, Math.ceil(listData.total / PAGE_SIZE))
    : 1;

  const canGoPrev = page > 0;
  const canGoNext = listData ? (page + 1) * PAGE_SIZE < listData.total : false;

  return {
    tourVersion: PORTAL_TOUR_VERSION,
    statusFilter,
    setStatusFilter,
    periodDays,
    setPeriodDays,
    page,
    setPage,
    pageSize: PAGE_SIZE,
    totalPages,
    canGoPrev,
    canGoNext,
    listData,
    topData,
    summary,
    loading,
    listError,
    topError,
    lastUpdatedAt,
    reload: load,
  };
}
