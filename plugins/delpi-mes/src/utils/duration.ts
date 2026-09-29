export function serverOffsetMs(referenceAt: string, clientNow = Date.now()): number {
  const reference = Date.parse(referenceAt);
  return Number.isFinite(reference) ? reference - clientNow : 0;
}

export function elapsedSeconds(startedAt: string | null, nowMs: number): number {
  if (!startedAt) return 0;
  const started = Date.parse(startedAt);
  if (!Number.isFinite(started)) return 0;
  return Math.max(0, Math.floor((nowMs - started) / 1000));
}

export function formatDuration(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map((value) => String(value).padStart(2, "0")).join(":");
}
