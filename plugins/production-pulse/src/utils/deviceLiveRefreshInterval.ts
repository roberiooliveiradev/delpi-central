import {
  POLL_INTERVAL_DEFAULT_MS,
  POLL_INTERVAL_MAX_MS,
  POLL_INTERVAL_MIN_MS,
  LIVE_UI_REFRESH_MIN_MS,
} from "../content/deviceValidationContent";

/**
 * Intervalo de refresh live da UI (detalhe admin + operador).
 * Segue pollIntervalMs do device, com piso de UI em content (liveUiRefreshMs.min).
 */
export function resolveDeviceLiveRefreshIntervalMs(
  pollIntervalMs: number | null | undefined,
): number {
  const ms =
    typeof pollIntervalMs === "number" && Number.isFinite(pollIntervalMs)
      ? pollIntervalMs
      : POLL_INTERVAL_DEFAULT_MS;
  const clamped = Math.min(
    POLL_INTERVAL_MAX_MS,
    Math.max(POLL_INTERVAL_MIN_MS, Math.round(ms)),
  );
  return Math.max(LIVE_UI_REFRESH_MIN_MS, clamped);
}

/** @deprecated Prefer resolveDeviceLiveRefreshIntervalMs — alias estável para operador. */
export function resolveOperatorRefreshIntervalMs(
  pollIntervalMs: number | null | undefined,
): number {
  return resolveDeviceLiveRefreshIntervalMs(pollIntervalMs);
}
