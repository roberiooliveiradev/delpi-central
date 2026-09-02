import { useCallback, useEffect, useState } from "react";

import {
  executeDeviceCommand,
  fetchDevice,
  fetchDeviceLive,
  pollDevice,
} from "../api/productionPulseApi";
import type { DeviceListItem } from "../types/device";
import type { DeviceDetailTab, LivePollResult } from "../types/detail";
import { resolveDeviceActionError } from "../utils/apiErrors";

type UseDeviceDetailOptions = {
  deviceId: string;
  enabled: boolean;
};

export function useDeviceDetail({ deviceId, enabled }: UseDeviceDetailOptions) {
  const [device, setDevice] = useState<DeviceListItem | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [liveSnapshot, setLiveSnapshot] = useState<LivePollResult | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [commandsRefreshToken, setCommandsRefreshToken] = useState(0);

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

  const applyDeviceActionFailure = async (err: unknown, fallback: string) => {
    await reloadDevice();
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
      setLiveSnapshot(polled);
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
    } catch (err) {
      await applyDeviceActionFailure(err, "Erro ao executar poll.");
    } finally {
      setRefreshing(false);
    }
  };

  const resetCounter = async () => {
    await executeDeviceCommand(deviceId, "reset");
    setCommandsRefreshToken((value) => value + 1);
    await pollNow();
    await reloadDevice();
  };

  return {
    device,
    loading,
    error,
    actionError,
    liveSnapshot,
    refreshing,
    commandsRefreshToken,
    reloadDevice,
    refreshLive,
    pollNow,
    resetCounter,
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
];
