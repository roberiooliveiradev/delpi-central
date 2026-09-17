import { resolveDeviceLiveRefreshIntervalMs } from "./deviceLiveRefreshInterval";

type DevicePollIntervalSource = {
  pollIntervalMs?: number | null;
};

/**
 * Intervalo de refresh live do mapa Admin (golpes/métricas).
 * Usa o menor pollIntervalMs dos IoTs visíveis — mesma família do operador.
 */
export function resolveHubDevicesLiveRefreshIntervalMs(
  devices: readonly DevicePollIntervalSource[],
): number {
  if (devices.length === 0) {
    return resolveDeviceLiveRefreshIntervalMs(undefined);
  }
  let minMs = Number.POSITIVE_INFINITY;
  for (const device of devices) {
    minMs = Math.min(minMs, resolveDeviceLiveRefreshIntervalMs(device.pollIntervalMs));
  }
  return Number.isFinite(minMs)
    ? minMs
    : resolveDeviceLiveRefreshIntervalMs(undefined);
}
