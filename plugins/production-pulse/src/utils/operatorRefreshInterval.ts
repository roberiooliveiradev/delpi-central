import {
  POLL_INTERVAL_DEFAULT_MS,
  POLL_INTERVAL_MAX_MS,
  POLL_INTERVAL_MIN_MS,
} from "../content/deviceValidationContent";

/**
 * Intervalo do refresh da superfície operador (GET device).
 * Segue o pollIntervalMs do device — sem piso artificial de 5 s.
 */
export function resolveOperatorRefreshIntervalMs(
  pollIntervalMs: number | null | undefined,
): number {
  const ms =
    typeof pollIntervalMs === "number" && Number.isFinite(pollIntervalMs)
      ? pollIntervalMs
      : POLL_INTERVAL_DEFAULT_MS;
  return Math.min(POLL_INTERVAL_MAX_MS, Math.max(POLL_INTERVAL_MIN_MS, Math.round(ms)));
}
