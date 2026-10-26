import type { DowntimeItem, DowntimeReasonOption, DowntimesQuery } from "../types/mes";
import type { BranchCode } from "../constants/routes";
import type { DowntimesRouteParams } from "../hooks/useDelpiMesRoute";
import { MES_BUSINESS_TIMEZONE, businessDayKey, zoneDayStartMs, zoneNextDayStartMs } from "./dayTimeline";

export type DowntimePeriodPreset = "today" | "7d" | "30d" | "custom";

export const DOWNTIME_PERIOD_PRESETS: ReadonlyArray<{ id: DowntimePeriodPreset; label: string }> = [
  { id: "today", label: "Hoje" },
  { id: "7d", label: "Últimos 7 dias" },
  { id: "30d", label: "Últimos 30 dias" },
  { id: "custom", label: "Período personalizado" },
];

const SOURCE_LABELS: Record<string, string> = {
  operator_pause: "Pausa do operador",
  automatic_detection: "Detecção automática",
  system: "Sistema",
  integration: "Integração",
  recovery: "Recuperação",
};

export function downtimeSourceLabel(source: string | null | undefined): string {
  if (!source) return "Não informado";
  return SOURCE_LABELS[source] ?? source;
}

function addCalendarDays(dayKey: string, deltaDays: number): string {
  const parts = dayKey.split("-").map(Number);
  const next = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + deltaDays));
  return next.toISOString().slice(0, 10);
}

function zoneDayStartIso(dayKey: string): string | undefined {
  const ms = zoneDayStartMs(dayKey, MES_BUSINESS_TIMEZONE);
  return ms === null ? undefined : new Date(ms).toISOString();
}

/** Converte a seleção de período da URL em intervalo ISO para o contrato.
 * Dias civis são avaliados no fuso operacional canônico (America/Sao_Paulo
 * — MES_BUSINESS_TIMEZONE), independente do fuso do navegador. Presets
 * usam limite inferior aberto (from = início do primeiro dia da janela);
 * em "custom", from/to são chaves de dia YYYY-MM-DD no fuso operacional e
 * o fim cobre o dia inteiro (limite exclusivo = início do dia seguinte). */
export function resolveDowntimePeriod(
  params: Pick<DowntimesRouteParams, "period" | "from" | "to">,
  now: Date = new Date(),
): { from?: string; to?: string } {
  const today = businessDayKey(now);
  if (params.period === "today") return { from: zoneDayStartIso(today) };
  if (params.period === "7d") return { from: zoneDayStartIso(addCalendarDays(today, -6)) };
  if (params.period === "30d") return { from: zoneDayStartIso(addCalendarDays(today, -29)) };
  const range: { from?: string; to?: string } = {};
  if (params.from) {
    const start = params.from ? zoneDayStartIso(params.from) : undefined;
    if (start) range.from = start;
  }
  if (params.to) {
    const end = zoneNextDayStartMs(params.to, MES_BUSINESS_TIMEZONE);
    if (end !== null) range.to = new Date(end).toISOString();
  }
  return range;
}

/** Monta a consulta enviada ao BFF — período resolvido + filtros de URL.
 * downtimeId (seleção/detalhe) nunca filtra a lista. */
export function buildDowntimesQuery(
  branch: BranchCode,
  params: DowntimesRouteParams,
  now: Date = new Date(),
): DowntimesQuery {
  const period = resolveDowntimePeriod(params, now);
  return {
    branch,
    workCenter: params.workCenter?.trim() || undefined,
    from: period.from,
    to: period.to,
    reasonCode: params.reasonCode || undefined,
    source: params.source || undefined,
    classification: params.classification || undefined,
    sort: params.sort === "oldest" ? "oldest" : "recent",
    page: Math.max(1, params.page),
    pageSize: params.pageSize,
  };
}

export function hasActiveDowntimeFilters(params: DowntimesRouteParams): boolean {
  return Boolean(
    params.workCenter ||
      params.reasonCode ||
      params.source ||
      params.classification ||
      params.sort === "oldest" ||
      params.period !== "7d" ||
      params.from ||
      params.to,
  );
}

/** Duração em segundos: fechada usa endedAt - startedAt; aberta usa o
 * relógio de referência do servidor (nowMs). Datas inválidas/ausentes
 * nunca viram 0s. */
export function downtimeDurationSeconds(item: DowntimeItem, nowMs: number): number | null {
  const started = item.startedAt ? Date.parse(item.startedAt) : NaN;
  if (!Number.isFinite(started)) return null;
  if (item.endedAt) {
    const ended = Date.parse(item.endedAt);
    return Number.isFinite(ended) && ended >= started ? Math.floor((ended - started) / 1000) : null;
  }
  return Math.max(0, Math.floor((nowMs - started) / 1000));
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const ms = Date.parse(iso);
  if (!Number.isFinite(ms)) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: MES_BUSINESS_TIMEZONE,
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(ms));
}

export function downtimeStatusLabel(item: DowntimeItem): { state: string; classification: string } {
  return {
    state: item.endedAt ? "Encerrada" : "Aberta",
    classification: item.confirmed ? "Confirmada" : "Pendente",
  };
}

export function reasonOptionsByCode(reasons: DowntimeReasonOption[]): Map<string, DowntimeReasonOption> {
  return new Map(reasons.map((reason) => [reason.code, reason]));
}
