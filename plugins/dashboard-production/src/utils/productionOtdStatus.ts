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

function startOfLocalDayMs(isoDate: string): number {
  return Date.parse(`${isoDate}T00:00:00`);
}

function todayIsoLocal(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function computeOtdStatus(
  plannedEndDate: string | null,
  actualEndDate: string | null,
  referenceDateIso: string = todayIsoLocal()
): ProductionOrderOtdStatus {
  if (!plannedEndDate) return "open";

  const planned = startOfLocalDayMs(plannedEndDate);
  if (Number.isNaN(planned)) return "open";

  if (!actualEndDate) {
    const reference = startOfLocalDayMs(referenceDateIso);
    if (Number.isNaN(reference)) return "open";
    // Due date já passou e ainda sem C2_DATRF → atrasada (mesmo critério da API).
    return planned < reference ? "late" : "open";
  }

  const actual = startOfLocalDayMs(actualEndDate);
  if (Number.isNaN(actual)) return "open";

  return actual <= planned ? "on_time" : "late";
}

export function computeDaysDiff(
  plannedEndDate: string | null,
  actualEndDate: string | null,
  referenceDateIso: string = todayIsoLocal()
): number | null {
  if (!plannedEndDate) return null;

  const planned = startOfLocalDayMs(plannedEndDate);
  if (Number.isNaN(planned)) return null;

  const endIso = actualEndDate || referenceDateIso;
  const end = startOfLocalDayMs(endIso);
  if (Number.isNaN(end)) return null;

  // Sem finalização e ainda no prazo: não há atraso a reportar.
  if (!actualEndDate && planned >= end) return null;

  const msPerDay = 24 * 60 * 60 * 1000;
  return Math.round((end - planned) / msPerDay);
}

export function readNumericField(value: unknown): number | null {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}
