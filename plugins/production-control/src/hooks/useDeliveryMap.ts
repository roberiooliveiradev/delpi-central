import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchDeliveryMap,
  patchDeliveryMapOverrides,
  refreshDeliveryMap,
} from "../api/ppcApi";
import { copy } from "../content/copy";
import type { DeliveryMapPayload, PpcBranch } from "../types";

export function useDeliveryMap(branch: PpcBranch, search: string) {
  const [data, setData] = useState<DeliveryMapPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchDeliveryMap({ branch, search, signal: controller.signal })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.deliveryMap.loadError);
        setData(null);
      })
      .finally(() => {
        if (controller.signal.aborted) return;
        setLoading(false);
      });
    return () => controller.abort();
  }, [branch, search, reloadToken]);

  const refreshFromTotvs = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const payload = await refreshDeliveryMap({ branch, search });
      setData(payload);
      return payload;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : copy.deliveryMap.loadError;
      setError(message);
      throw err;
    } finally {
      setRefreshing(false);
    }
  }, [branch, search]);

  const saveOverrides = useCallback(
    async (
      updates: Array<{
        production_order: string;
        mp_ok?: boolean;
        work_center?: string;
      }>,
    ) => {
      if (updates.length === 0) return data;
      setSaving(true);
      setError(null);
      try {
        const payload = await patchDeliveryMapOverrides({ branch, search, updates });
        setData(payload);
        return payload;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : copy.deliveryMap.loadError;
        setError(message);
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [branch, data, search],
  );

  return {
    data,
    loading,
    refreshing,
    saving,
    error,
    reload,
    refreshFromTotvs,
    saveOverrides,
    applyPayload: setData,
  };
}

/** Debounce de PATCH para MP-OK / CT sem spammar o BFF. */
export function useDeliveryMapOverrideSaver(
  saveOverrides: ReturnType<typeof useDeliveryMap>["saveOverrides"],
  debounceMs = 400,
) {
  const timerRef = useRef<number | null>(null);
  const pendingRef = useRef<
    Map<string, { production_order: string; mp_ok?: boolean; work_center?: string }>
  >(new Map());

  const flush = useCallback(() => {
    const updates = Array.from(pendingRef.current.values());
    pendingRef.current.clear();
    if (updates.length === 0) return Promise.resolve(undefined);
    return saveOverrides(updates);
  }, [saveOverrides]);

  const queue = useCallback(
    (update: { production_order: string; mp_ok?: boolean; work_center?: string }) => {
      const key = update.production_order;
      const prev = pendingRef.current.get(key) ?? { production_order: key };
      pendingRef.current.set(key, { ...prev, ...update });
      if (timerRef.current != null) {
        window.clearTimeout(timerRef.current);
      }
      timerRef.current = window.setTimeout(() => {
        timerRef.current = null;
        void flush();
      }, debounceMs);
    },
    [debounceMs, flush],
  );

  useEffect(
    () => () => {
      if (timerRef.current != null) {
        window.clearTimeout(timerRef.current);
      }
    },
    [],
  );

  return { queue, flush };
}
