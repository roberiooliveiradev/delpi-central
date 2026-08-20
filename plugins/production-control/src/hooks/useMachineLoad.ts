import { useCallback, useEffect, useState } from "react";

import { fetchMachineLoad, refreshMachineLoad } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { MachineLoadPayload, PpcBranch } from "../types";

type UseMachineLoadParams = {
  branch: PpcBranch;
  workCenter: string | null;
  startDate: string | null;
  endDate: string | null;
};

export function useMachineLoad({ branch, workCenter, startDate, endDate }: UseMachineLoadParams) {
  const [data, setData] = useState<MachineLoadPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchMachineLoad({ branch, workCenter, startDate, endDate, signal: controller.signal })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.machineLoad.loadError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
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
      return payload;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : copy.machineLoad.loadError;
      setError(message);
      throw err;
    } finally {
      setRefreshing(false);
    }
  }, [branch, workCenter, startDate, endDate]);

  return { data, loading, refreshing, error, reload, refreshFromTotvs, applyPayload: setData };
}
