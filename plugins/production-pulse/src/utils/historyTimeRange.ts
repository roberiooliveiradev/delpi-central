import type { ChartPoint } from "./detailDisplay";

export type HistoryRangePreset =
  | "1m"
  | "15m"
  | "1h"
  | "24h"
  | "7d"
  | "30d"
  | "month"
  | "90d"
  | "12m"
  | "custom";

type HistoryRollingPresetOption = {
  value: Exclude<HistoryRangePreset, "custom" | "month" | "12m">;
  label: string;
  mode: "rolling";
  durationMs: number;
};

type HistoryCalendarMonthPresetOption = {
  value: "month";
  label: string;
  mode: "calendarMonth";
};

type HistoryRollingMonthsPresetOption = {
  value: "12m";
  label: string;
  mode: "rollingMonths";
  months: number;
};

export type HistoryRangePresetOption =
  | HistoryRollingPresetOption
  | HistoryCalendarMonthPresetOption
  | HistoryRollingMonthsPresetOption;

export const HISTORY_RANGE_PRESET_OPTIONS: readonly HistoryRangePresetOption[] = [
  { value: "1m", label: "1 min", mode: "rolling", durationMs: 60_000 },
  { value: "15m", label: "15 min", mode: "rolling", durationMs: 15 * 60_000 },
  { value: "1h", label: "1 h", mode: "rolling", durationMs: 60 * 60_000 },
  { value: "24h", label: "24 h", mode: "rolling", durationMs: 24 * 60 * 60_000 },
  { value: "7d", label: "7 dias", mode: "rolling", durationMs: 7 * 24 * 60 * 60_000 },
  { value: "30d", label: "30 dias", mode: "rolling", durationMs: 30 * 24 * 60 * 60_000 },
  { value: "month", label: "Este mês", mode: "calendarMonth" },
  { value: "90d", label: "90 dias", mode: "rolling", durationMs: 90 * 24 * 60 * 60_000 },
  { value: "12m", label: "12 meses", mode: "rollingMonths", months: 12 },
] as const;

export type ChartTickGranularity = "second" | "minute" | "hour" | "day";

const CHART_TARGET_POINTS = 96;
export const HISTORY_CHART_PAGE_SIZE_MAX = 500;
/** Teto alinhado à API (`sampleIntervalMs`) — períodos Livre longos (meses). */
export const HISTORY_CHART_SAMPLE_INTERVAL_MS_MAX = 366 * 86_400_000;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

function resolveSpanMs(fromIso: string | undefined, toIso: string | undefined): number {
  const fromMs = fromIso ? new Date(fromIso).getTime() : NaN;
  const toMs = toIso ? new Date(toIso).getTime() : Date.now();
  if (Number.isFinite(fromMs) && Number.isFinite(toMs) && toMs >= fromMs) {
    return Math.max(toMs - fromMs, 1);
  }
  return 60 * 60_000;
}

/** Valor para o filtro datetime-local no fuso local. */
export function toDatetimeLocalValue(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}T${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}

export function datetimeLocalToIso(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const date = new Date(trimmed);
  if (Number.isNaN(date.getTime())) return undefined;
  return date.toISOString();
}

export function isoToDatetimeLocalValue(iso: string | undefined): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return toDatetimeLocalValue(date);
}

export function resolveDefaultHistoryPreset(pollIntervalMs: number): Exclude<HistoryRangePreset, "custom"> {
  const poll = Number.isFinite(pollIntervalMs) && pollIntervalMs > 0 ? pollIntervalMs : 1000;
  if (poll <= 1000) return "1m";
  if (poll <= 10_000) return "15m";
  if (poll <= 60_000) return "1h";
  return "24h";
}

export function boundsForHistoryPreset(
  preset: Exclude<HistoryRangePreset, "custom">,
  nowMs: number = Date.now(),
): { fromIso: string; toIso: string } {
  const option = HISTORY_RANGE_PRESET_OPTIONS.find((item) => item.value === preset);
  const to = new Date(nowMs);

  if (option?.mode === "calendarMonth") {
    const from = new Date(to.getFullYear(), to.getMonth(), 1, 0, 0, 0, 0);
    return { fromIso: from.toISOString(), toIso: to.toISOString() };
  }

  if (option?.mode === "rollingMonths") {
    const from = new Date(nowMs);
    from.setMonth(from.getMonth() - option.months);
    return { fromIso: from.toISOString(), toIso: to.toISOString() };
  }

  const durationMs = option?.mode === "rolling" ? option.durationMs : 60 * 60_000;
  const from = new Date(nowMs - durationMs);
  return { fromIso: from.toISOString(), toIso: to.toISOString() };
}

/**
 * Granularidade do eixo X pelo **intervalo exibido** (não pelo poll).
 * Poll rápido não deve forçar segundos em janelas de horas/dias.
 */
export function resolveChartTickGranularity(
  fromIso: string | undefined,
  toIso: string | undefined,
  _pollIntervalMs?: number,
): ChartTickGranularity {
  const spanMs = resolveSpanMs(fromIso, toIso);
  if (spanMs <= 5 * 60_000) return "second";
  if (spanMs <= 6 * 60 * 60_000) return "minute";
  if (spanMs <= 7 * 24 * 60 * 60_000) return "hour";
  return "day";
}

export function formatChartTick(iso: string, granularity: ChartTickGranularity): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  if (granularity === "second") {
    return new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(date);
  }
  if (granularity === "minute") {
    return new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }
  if (granularity === "hour") {
    return new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
  }).format(date);
}

/** Quantidade de pontos a pedir à API para cobrir o intervalo sem saturar. */
export function resolveHistoryChartPageSize(
  fromIso: string | undefined,
  toIso: string | undefined,
  pollIntervalMs: number,
): number {
  const spanMs = resolveSpanMs(fromIso, toIso);
  const poll = Number.isFinite(pollIntervalMs) && pollIntervalMs > 0 ? pollIntervalMs : 1000;
  const expected = Math.ceil(spanMs / poll) + 4;
  return Math.min(HISTORY_CHART_PAGE_SIZE_MAX, Math.max(48, expected));
}

/**
 * Intervalo de amostragem uniforme no servidor quando o período tem mais leituras
 * do que o pageSize do gráfico. Sem isso, o LIMIT pega só o fim da janela.
 */
export function resolveHistoryChartSampleIntervalMs(
  fromIso: string | undefined,
  toIso: string | undefined,
  pollIntervalMs: number,
  targetPoints: number = CHART_TARGET_POINTS,
): number | undefined {
  const spanMs = resolveSpanMs(fromIso, toIso);
  const poll = Number.isFinite(pollIntervalMs) && pollIntervalMs > 0 ? pollIntervalMs : 1000;
  const expectedRaw = Math.ceil(spanMs / poll);
  if (expectedRaw <= HISTORY_CHART_PAGE_SIZE_MAX) {
    return undefined;
  }
  const points = Math.max(8, Math.min(targetPoints, HISTORY_CHART_PAGE_SIZE_MAX));
  const ideal = Math.max(poll, Math.ceil(spanMs / points));
  return Math.min(HISTORY_CHART_SAMPLE_INTERVAL_MS_MAX, ideal);
}

export type HistoryReadingsResolution = "raw" | "hour" | "day";

const HISTORY_RESOLUTION_HOUR_AFTER_MS = 7 * 24 * 60 * 60_000;
const HISTORY_RESOLUTION_DAY_AFTER_MS = 90 * 24 * 60 * 60_000;

/**
 * R51 — spans longos preferem rollup na API; raw denso permanece para janelas curtas.
 */
export function resolveHistoryReadingsResolution(
  fromIso: string | undefined,
  toIso: string | undefined,
): HistoryReadingsResolution {
  const spanMs = resolveSpanMs(fromIso, toIso);
  if (spanMs > HISTORY_RESOLUTION_DAY_AFTER_MS) return "day";
  if (spanMs > HISTORY_RESOLUTION_HOUR_AFTER_MS) return "hour";
  return "raw";
}

/** Reduz pontos densos mantendo início/fim e passo uniforme. */
export function downsampleChartPoints(points: ChartPoint[], maxPoints = CHART_TARGET_POINTS): ChartPoint[] {
  if (points.length <= maxPoints) return points;
  if (maxPoints < 3) return points.slice(0, maxPoints);

  const lastIndex = points.length - 1;
  const innerSlots = maxPoints - 2;
  const result: ChartPoint[] = [points[0]!];
  for (let slot = 1; slot <= innerSlots; slot += 1) {
    const index = Math.round((slot * lastIndex) / (innerSlots + 1));
    const point = points[index];
    if (point && result[result.length - 1] !== point) {
      result.push(point);
    }
  }
  const last = points[lastIndex]!;
  if (result[result.length - 1] !== last) {
    result.push(last);
  }
  return result;
}

export function applyAdaptiveChartLabels(
  points: ChartPoint[],
  granularity: ChartTickGranularity,
): ChartPoint[] {
  return points.map((point) => ({
    ...point,
    label: formatChartTick(point.x, granularity),
  }));
}
