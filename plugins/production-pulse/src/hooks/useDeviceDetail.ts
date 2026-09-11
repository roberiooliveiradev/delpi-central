import { useCallback, useEffect, useState } from "react";

import {
  executeDeviceCommand,
  fetchDevice,
  fetchDeviceLive,
  pollDevice,
} from "../api/productionPulseApi";
import { ProductionPulseRequestError } from "../api/httpClient";
import type { DeviceListItem } from "../types/device";
import type { DeviceDetailTab, LivePollResult } from "../types/detail";
import {
  isDeviceConnectivityError,
  resolveDeviceActionError,
} from "../utils/apiErrors";
import { useDeviceLiveRefresh } from "./useDeviceLiveRefresh";

export type LiveConnectivityIssue = {
  code?: string;
  message: string;
};

type UseDeviceDetailOptions = {
  deviceId: string;
  enabled: boolean;
};

export function useDeviceDetail({ deviceId, enabled }: UseDeviceDetailOptions) {
  const [device, setDevice] = useState<DeviceListItem | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [liveConnectivityIssue, setLiveConnectivityIssue] =
    useState<LiveConnectivityIssue | null>(null);
  const [liveSnapshot, setLiveSnapshot] = useState<LivePollResult | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [commandsRefreshToken, setCommandsRefreshToken] = useState(0);
  const [historyRefreshToken, setHistoryRefreshToken] = useState(0);

  const reloadDevice = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const row = await fetchDevice(deviceId);
      setDevice(row);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dispositivo.");
      setLoading(false);
    }
  }, [deviceId, enabled]);

  useEffect(() => {
    void reloadDevice();
  }, [reloadDevice]);

  const applyLiveSnapshot = useCallback((live: LivePollResult) => {
    setLiveConnectivityIssue(null);
    setLiveSnapshot(live);
    setDevice((current) =>
      current
        ? {
            ...current,
            lastMetrics: live.metrics,
            lastSeenAt: live.recordedAt,
            status: live.status as DeviceListItem["status"],
            online: live.online,
          }
        : current,
    );
  }, []);

  const recordLiveConnectivityFailure = useCallback((err: unknown) => {
    if (!isDeviceConnectivityError(err)) return;
    const message =
      err instanceof ProductionPulseRequestError
        ? err.message
        : "Não foi possível falar com o dispositivo.";
    setLiveConnectivityIssue({
      code: err instanceof ProductionPulseRequestError ? err.code : undefined,
      message,
    });
  }, []);

  const quietLiveRefresh = useCallback(async () => {
    if (!enabled) return;
    try {
      const live = await fetchDeviceLive(deviceId);
      applyLiveSnapshot(live);
    } catch (err) {
      recordLiveConnectivityFailure(err);
    }
  }, [applyLiveSnapshot, deviceId, enabled, recordLiveConnectivityFailure]);

  useDeviceLiveRefresh({
    enabled: enabled && Boolean(device),
    pollIntervalMs: device?.pollIntervalMs,
    onTick: quietLiveRefresh,
  });

  useEffect(() => {
    if (!enabled) return;
    void quietLiveRefresh();
  }, [deviceId, enabled]); // carga inicial de live/saúde ao abrir o detalhe

  const applyDeviceActionFailure = async (err: unknown, fallback: string) => {
    await reloadDevice();
    recordLiveConnectivityFailure(err);
    const resolved = resolveDeviceActionError(err, fallback);
    if (resolved.kind === "device") {
      setActionError(resolved.message);
      return;
    }
    setActionError(null);
    setError(resolved.message);
  };

  const refreshLive = async () => {
    if (!device) return;
    setRefreshing(true);
    setActionError(null);
    try {
      const live = await fetchDeviceLive(deviceId);
      applyLiveSnapshot(live);
    } catch (err) {
      await applyDeviceActionFailure(err, "Erro ao ler device ao vivo.");
    } finally {
      setRefreshing(false);
    }
  };

  const pollNow = async () => {
    if (!device) return;
    setRefreshing(true);
    setActionError(null);
    try {
      const polled = await pollDevice(deviceId);
      setLiveConnectivityIssue(null);
      setLiveSnapshot((current) => ({
        ...polled,
        firmwareVersion: current?.firmwareVersion ?? polled.firmwareVersion,
        uptimeMs: current?.uptimeMs ?? polled.uptimeMs,
        freeHeap: current?.freeHeap ?? polled.freeHeap,
        rssi: current?.rssi ?? polled.rssi,
        wifiConnected: current?.wifiConnected ?? polled.wifiConnected,
      }));
      setDevice((current) =>
        current
          ? {
              ...current,
              lastMetrics: polled.metrics,
              lastSeenAt: polled.recordedAt,
              status: polled.status as DeviceListItem["status"],
              online: polled.online,
            }
          : current,
      );
      setHistoryRefreshToken((value) => value + 1);
      setCommandsRefreshToken((value) => value + 1);
      try {
        const live = await fetchDeviceLive(deviceId);
        applyLiveSnapshot(live);
      } catch (err) {
        recordLiveConnectivityFailure(err);
      }
    } catch (err) {
      await applyDeviceActionFailure(err, "Erro ao executar poll.");
    } finally {
      setRefreshing(false);
    }
  };

  const resetCounter = async () => {
    await executeDeviceCommand(deviceId, "reset");
    setCommandsRefreshToken((value) => value + 1);
    setHistoryRefreshToken((value) => value + 1);
    await pollNow();
    await reloadDevice();
  };

  const factoryReset = async () => {
    await executeDeviceCommand(deviceId, "factory_reset");
    setCommandsRefreshToken((value) => value + 1);
    await reloadDevice();
  };

  return {
    device,
    loading,
    error,
    actionError,
    liveConnectivityIssue,
    liveSnapshot,
    refreshing,
    commandsRefreshToken,
    historyRefreshToken,
    reloadDevice,
    refreshLive,
    pollNow,
    resetCounter,
    factoryReset,
  };
}

export type DeviceDetailNavItem = {
  id: DeviceDetailTab;
  label: string;
  hint?: string;
};

export const DEVICE_DETAIL_NAV: DeviceDetailNavItem[] = [
  { id: "overview", label: "Visão geral" },
  { id: "history", label: "Histórico" },
  { id: "commands", label: "Comandos" },
  { id: "firmware", label: "Firmware" },
  { id: "hardware", label: "Hardware" },
];
