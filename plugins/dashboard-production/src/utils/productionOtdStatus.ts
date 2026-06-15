import type { ProductionOrderOtdStatus } from "../types/production";

export function resolveProtheusOrIsoDate(value: unknown): string | null {
  if (value == null || value === "") return null;
  const trimmed = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return trimmed;
  if (/^\d{8}$/.test(trimmed)) {
    return `${trimmed.slice(0, 4)}-${trimmed.slice(4, 6)}-${trimmed.slice(6, 8)}`;
  }
  return null;
}

export function computeOtdStatus(
  plannedEndDate: string | null,
  actualEndDate: string | null
): ProductionOrderOtdStatus {
  if (!actualEndDate) return "open";
  if (!plannedEndDate) return "open";

  const planned = Date.parse(`${plannedEndDate}T00:00:00`);
  const actual = Date.parse(`${actualEndDate}T00:00:00`);
  if (Number.isNaN(planned) || Number.isNaN(actual)) return "open";

  return actual <= planned ? "on_time" : "late";
}

export function computeDaysDiff(
  plannedEndDate: string | null,
  actualEndDate: string | null
): number | null {
  if (!plannedEndDate || !actualEndDate) return null;

  const planned = Date.parse(`${plannedEndDate}T00:00:00`);
  const actual = Date.parse(`${actualEndDate}T00:00:00`);
  if (Number.isNaN(planned) || Number.isNaN(actual)) return null;

  const msPerDay = 24 * 60 * 60 * 1000;
  return Math.round((actual - planned) / msPerDay);
}

export function readNumericField(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}
