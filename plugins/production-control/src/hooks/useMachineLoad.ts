import { useCallback, useEffect, useRef, useState } from "react";

import { fetchMachineLoad, refreshMachineLoad } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { MachineLoadPayload, PpcBranch } from "../types";

type UseMachineLoadParams = {
  branch: PpcBranch;
  workCenter: string | null;
  startDate: string | null;
  endDate: string | null;
};

function scopeKey(
  branch: PpcBranch,
  startDate: string | null,
  endDate: string | null,
): string {
  return `${branch}|${startDate ?? ""}|${endDate ?? ""}`;
}

/**
 * Carga o snapshot da fila. Trocar só o CT não zera a tela com «Carregando…»:
 * o BFF já tem a fila da filial; o custo era o enrich HZA + spinner no MFE.
 */
export function useMachineLoad({ branch, workCenter, startDate, endDate }: UseMachineLoadParams) {
  const [data, setData] = useState<MachineLoadPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [switchingCenter, setSwitchingCenter] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const loadedScopeRef = useRef<string | null>(null);
  const hasDataRef = useRef(false);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    hasDataRef.current = data != null;
  }, [data]);

  useEffect(() => {
    const controller = new AbortController();
    const nextScope = scopeKey(branch, startDate, endDate);
    const softCenterSwitch =
      hasDataRef.current && loadedScopeRef.current === nextScope;

    if (softCenterSwitch) {
      setSwitchingCenter(true);
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          selected: {
            ...prev.selected,
            work_center: workCenter,
            requested_work_center: workCenter,
            items: [],
          },
        };
      });
    } else {
      setLoading(true);
      setSwitchingCenter(false);
    }

    fetchMachineLoad({ branch, workCenter, startDate, endDate, signal: controller.signal })
      .then((payload) => {
        setData(payload);
        setError(null);
        loadedScopeRef.current = nextScope;
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.machineLoad.loadError);
        if (!softCenterSwitch) {
          setData(null);
          loadedScopeRef.current = null;
        }
      })
      .finally(() => {
        if (controller.signal.aborted) return;
        setLoading(false);
        setSwitchingCenter(false);
      });
    return () => controller.abort();
  }, [branch, workCenter, startDate, endDate, reloadToken]);

  const refreshFromTotvs = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const payload = await refreshMachineLoad({
        branch,
        workCenter,
        startDate,
        endDate,
      });
      setData(payload);
      loadedScopeRef.current = scopeKey(branch, startDate, endDate);
      return payload;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : copy.machineLoad.loadError;
      setError(message);
      throw err;
    } finally {
      setRefreshing(false);
    }
  }, [branch, workCenter, startDate, endDate]);

  return {
    data,
    loading,
    switchingCenter,
    refreshing,
    error,
    reload,
    refreshFromTotvs,
    applyPayload: setData,
  };
}
