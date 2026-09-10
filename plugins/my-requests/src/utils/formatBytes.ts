/** Human-readable byte size for attachment cards and bubbles. */
export function formatBytes(value: number | null | undefined): string | undefined {
  if (value == null || !Number.isFinite(value) || value < 0) return undefined;
  if (value < 1024) return `${Math.round(value)} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}
