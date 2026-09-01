import { useCallback, useEffect, useState } from "react";

import { fetchDeviceSummary, fetchDevices, pollDevice } from "../api/productionPulseApi";
import type { DeviceListItem, DeviceSummary } from "../types/device";
import { applyClientFilters } from "../utils/deviceGrouping";
import type { PanelFilters } from "../utils/panelFilterUrl";

type PanelDataState = {
  summary: DeviceSummary | null;
  devices: DeviceListItem[];
  filteredDevices: DeviceListItem[];
  loading: boolean;
  error: string | null;
  pollingDeviceId: string | null;
};

export function usePanelData(filters: PanelFilters, enabled: boolean) {
  const [state, setState] = useState<PanelDataState>({
    summary: null,
    devices: [],
    filteredDevices: [],
    loading: enabled,
    error: null,
    pollingDeviceId: null,
  });

  const reload = useCallback(async (signal?: AbortSignal) => {
    if (!enabled) return;
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const [summary, devices] = await Promise.all([
        fetchDeviceSummary(filters.branch, { signal }),
        fetchDevices({
          branch: filters.branch,
          role: filters.role || undefined,
          search: filters.search || undefined,
          signal,
        }),
      ]);
      const filteredDevices = applyClientFilters(devices, {
        status: filters.status,
        anchorType: filters.anchorType,
      });
      setState((current) => ({
        ...current,
        summary,
        devices,
        filteredDevices,
        loading: false,
        error: null,
      }));
    } catch (err) {
      if (signal?.aborted) return;
      setState((current) => ({
        ...current,
        loading: false,
        error: err instanceof Error ? err.message : "Erro ao carregar dispositivos.",
      }));
    }
  }, [enabled, filters.anchorType, filters.branch, filters.role, filters.search, filters.status]);

  useEffect(() => {
    if (!enabled) {
      setState((current) => ({ ...current, loading: false }));
      return;
    }
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [enabled, reload]);

  const runPoll = async (deviceId: string) => {
    setState((current) => ({ ...current, pollingDeviceId: deviceId }));
    try {
      await pollDevice(deviceId);
      await reload();
    } catch (err) {
      setState((current) => ({
        ...current,
        error: err instanceof Error ? err.message : "Falha ao atualizar dispositivo.",
      }));
    } finally {
      setState((current) => ({ ...current, pollingDeviceId: null }));
    }
  };

  return {
    ...state,
    reload: () => reload(),
    runPoll,
  };
}
