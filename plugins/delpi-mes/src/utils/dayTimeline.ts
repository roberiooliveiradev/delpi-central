import { todayIsoInTimeZone } from "@delpi/plugin-ui/index";

import type { WorkCenterTimelineItem } from "../types/mes";
import { downtimeReasonDisplay } from "./monitoringPresentation";

export type DayEventTone = "default" | "success" | "warning" | "danger" | "info";
export type DayEventPresentation = { label: string; tone: DayEventTone; pendingReason: boolean };

const TIME_FORMAT = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });

export function startOfLocalDayIso(now = new Date()): string {
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  return start.toISOString();
}

export function localDayKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Fuso operacional canônico do MES — mesma convenção do Production Control
 * (FACTORY_TIMEZONE) e do plugin-ui (periodPreset): o dia civil do chão de
 * fábrica e America/Sao_Paulo, independente do fuso do navegador. */
export const MES_BUSINESS_TIMEZONE = "America/Sao_Paulo";

/** Chave de dia YYYY-MM-DD no fuso operacional (reutiliza o helper canônico
 * do plugin-ui — funciona para qualquer instante, nao só "hoje"). */
export function businessDayKey(
  date: Date,
  timeZone: string = MES_BUSINESS_TIMEZONE,
): string {
  return todayIsoInTimeZone(date, timeZone);
}

/** Início do dia civil YYYY-MM-DD no fuso operacional, como instante (ms).
 * Resolve o offset real da zona via Intl — não assume -03:00 fixo, então
 * regras históricas de horário de verão continuam corretas. Retorna null
 * para chave inválida. */
export function zoneDayStartMs(
  dayKey: string,
  timeZone: string = MES_BUSINESS_TIMEZONE,
): number | null {
  const parts = dayKey.split("-");
  if (parts.length !== 3) return null;
  const year = Number(parts[0]);
  const month = Number(parts[1]);
  const day = Number(parts[2]);
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) {
    return null;
  }
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > 31) return null;
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  const target = Date.UTC(year, month - 1, day, 0, 0, 0);
  let guess = target - 3 * 60 * 60 * 1000;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    const zoneParts = formatter.formatToParts(new Date(guess));
    const wallAsUtc = Date.UTC(
      Number(zoneParts.find((p) => p.type === "year")?.value ?? "0"),
      Number(zoneParts.find((p) => p.type === "month")?.value ?? "0") - 1,
      Number(zoneParts.find((p) => p.type === "day")?.value ?? "0"),
      Number(zoneParts.find((p) => p.type === "hour")?.value ?? "0"),
      Number(zoneParts.find((p) => p.type === "minute")?.value ?? "0"),
      Number(zoneParts.find((p) => p.type === "second")?.value ?? "0"),
    );
    const next = target - (wallAsUtc - guess);
    if (next === guess) break;
    guess = next;
  }
  return guess;
}

/** Início do dia seguinte no fuso operacional (limite exclusivo canônico),
 * como instante (ms). */
export function zoneNextDayStartMs(
  dayKey: string,
  timeZone: string = MES_BUSINESS_TIMEZONE,
): number | null {
  const parts = dayKey.split("-").map(Number);
  if (parts.length !== 3 || parts.some((n) => !Number.isInteger(n))) return null;
  const dayAfter = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + 1));
  const nextKey = todayIsoInTimeZone(dayAfter, "UTC");
  return zoneDayStartMs(nextKey, timeZone);
}

/** Intervalo [início, fim) do dia civil no fuso operacional; quando o dia é
 * o corrente, o fim aberto fica ausente (mesma semântica de dayRangeIso). */
export function businessDayRangeIso(
  dayKey: string | null,
  now: Date = new Date(),
  timeZone: string = MES_BUSINESS_TIMEZONE,
): { from: string; to?: string } {
  const todayKey = businessDayKey(now, timeZone);
  const key = dayKey ?? todayKey;
  const start = zoneDayStartMs(key, timeZone);
  if (start === null) {
    const fallback = zoneDayStartMs(todayKey, timeZone) ?? Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
    return { from: new Date(fallback).toISOString() };
  }
  if (key === todayKey) return { from: new Date(start).toISOString() };
  const end = zoneNextDayStartMs(key, timeZone);
  return { from: new Date(start).toISOString(), to: end === null ? undefined : new Date(end).toISOString() };
}

/** Horário hh:mm no fuso operacional para a apresentação de paradas. */
export function formatBusinessClock(
  ms: number,
  timeZone: string = MES_BUSINESS_TIMEZONE,
): string {
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(ms));
}

export function endOfLocalDayMs(dayStartMs: number): number {
  const end = new Date(dayStartMs);
  end.setHours(23, 59, 59, 999);
  return end.getTime();
}

export function dayRangeIso(dayKey?: string | null, now = new Date()): { from: string; to?: string } {
  const start = new Date(now);
  if (dayKey) {
    const [year, month, day] = dayKey.split("-").map(Number);
    if (year && month && day) start.setFullYear(year, month - 1, day);
  }
  start.setHours(0, 0, 0, 0);
  if (start.getTime() > now.getTime() || localDayKey(start) === localDayKey(now)) {
    const today = new Date(now);
    today.setHours(0, 0, 0, 0);
    return { from: today.toISOString() };
  }
  return { from: start.toISOString(), to: new Date(endOfLocalDayMs(start.getTime())).toISOString() };
}

export function presentDayState(state: string): { label: string; tone: DayEventTone } {
  switch (state) {
    case "producing":
      return { label: "Produzindo", tone: "success" };
    case "stopped":
      return { label: "Parada", tone: "danger" };
    case "setup":
      return { label: "Setup", tone: "warning" };
    case "planned_stop":
      return { label: "Parada planejada", tone: "info" };
    case "idle":
      return { label: "Livre", tone: "default" };
    default:
      return { label: "Estado indisponível", tone: "default" };
  }
}

export function presentDayEvent(item: WorkCenterTimelineItem): DayEventPresentation {
  const pendingReason = Boolean(item.downtime && (!item.downtime.confirmed || !item.downtime.reasonCode));
  return { ...presentDayState(item.state), pendingReason };
}

export function dayEventDurationSeconds(item: WorkCenterTimelineItem, fromIso: string, toIso: string, nowMs: number): number {
  const startedAt = Date.parse(item.startedAt);
  const from = Date.parse(fromIso);
  const to = Date.parse(toIso);
  if (!Number.isFinite(startedAt) || !Number.isFinite(from)) return 0;
  const start = Math.max(startedAt, from);
  const endedAt = item.endedAt === null ? null : Date.parse(item.endedAt);
  const end = endedAt === null ? nowMs : Math.min(endedAt, Number.isFinite(to) ? to : endedAt);
  return Math.max(0, Math.floor((end - start) / 1000));
}

export function formatDayEventRange(item: WorkCenterTimelineItem, fromIso: string, toIso: string, nowMs: number): string {
  const startedAt = Date.parse(item.startedAt);
  const from = Date.parse(fromIso);
  if (!Number.isFinite(startedAt)) return "—";
  const startLabel = TIME_FORMAT.format(new Date(Math.max(startedAt, Number.isFinite(from) ? from : startedAt)));
  if (item.endedAt === null) return `${startLabel} → agora`;
  const to = Date.parse(toIso);
  const endMs = Math.min(Date.parse(item.endedAt), Number.isFinite(to) ? to : nowMs);
  return `${startLabel} → ${TIME_FORMAT.format(new Date(endMs))}`;
}

export function dayEventContext(item: WorkCenterTimelineItem): string {
  const parts: string[] = [];
  if (item.productionOrder) parts.push(`OP ${item.productionOrder}`);
  if (item.operationCode) parts.push(`Operação ${item.operationCode}`);
  return parts.join(" · ");
}

export function dayEventReason(item: WorkCenterTimelineItem, presentation: DayEventPresentation): string | null {
  if (item.state !== "stopped") return null;
  if (presentation.pendingReason) return "Motivo pendente";
  return downtimeReasonDisplay(item.downtime) ?? "Motivo não informado";
}

export type DaySegment = {
  startMs: number;
  endMs: number;
  state: string;
  item: WorkCenterTimelineItem | null;
};

export function buildDaySegments(items: WorkCenterTimelineItem[], fromIso: string, nowMs: number): DaySegment[] {
  const from = Date.parse(fromIso);
  if (!Number.isFinite(from)) return [];
  const dayEnd = endOfLocalDayMs(from);
  const clipEnd = Math.min(nowMs, dayEnd);
  const sorted = [...items]
    .filter((item) => Number.isFinite(Date.parse(item.startedAt)))
    .sort((a, b) => Date.parse(a.startedAt) - Date.parse(b.startedAt));
  const segments: DaySegment[] = [];
  let cursor = from;
  for (const item of sorted) {
    const start = Math.max(Date.parse(item.startedAt), from);
    const rawEnd = item.endedAt === null ? clipEnd : Date.parse(item.endedAt);
    const end = Math.min(Number.isFinite(rawEnd) ? rawEnd : clipEnd, dayEnd);
    if (end <= start) continue;
    if (start > cursor) segments.push({ startMs: cursor, endMs: start, state: "inactive", item: null });
    segments.push({ startMs: start, endMs: end, state: item.state, item });
    cursor = Math.max(cursor, end);
  }
  if (cursor < dayEnd) segments.push({ startMs: cursor, endMs: dayEnd, state: "inactive", item: null });
  return segments;
}

export type DaySummary = {
  producingSec: number;
  stoppedSec: number;
  stops: number;
  availabilityPct: number | null;
};

export function summarizeDay(segments: DaySegment[], fromIso: string, nowMs: number): DaySummary {
  const from = Date.parse(fromIso);
  const elapsed = Math.max(0, Math.min(nowMs, Number.isFinite(from) ? endOfLocalDayMs(from) : nowMs) - from);
  let producingSec = 0;
  let stoppedSec = 0;
  let stops = 0;
  for (const segment of segments) {
    const duration = Math.max(0, segment.endMs - segment.startMs) / 1000;
    if (segment.state === "producing") producingSec += duration;
    if (segment.state === "stopped") { stoppedSec += duration; stops += 1; }
  }
  return {
    producingSec: Math.floor(producingSec),
    stoppedSec: Math.floor(stoppedSec),
    stops,
    availabilityPct: elapsed > 0 ? Math.round((producingSec * 1000 * 100) / elapsed) : null,
  };
}

export type DowntimeReasonTotal = { label: string; seconds: number };

export function downtimeReasonTotals(segments: DaySegment[]): DowntimeReasonTotal[] {
  const totals = new Map<string, number>();
  for (const segment of segments) {
    if (segment.state !== "stopped" || !segment.item) continue;
    const presentation = presentDayEvent(segment.item);
    const label = presentation.pendingReason
      ? "Sem motivo informado"
      : downtimeReasonDisplay(segment.item.downtime) ?? "Sem motivo informado";
    totals.set(label, (totals.get(label) ?? 0) + Math.max(0, segment.endMs - segment.startMs) / 1000);
  }
  return Array.from(totals.entries())
    .map(([label, seconds]) => ({ label, seconds: Math.floor(seconds) }))
    .sort((a, b) => b.seconds - a.seconds);
}

export function formatHoursMinutes(totalSeconds: number): string {
  const minutes = Math.max(0, Math.floor(totalSeconds / 60));
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${String(minutes % 60).padStart(2, "0")}min`;
}

export function formatDayClock(ms: number): string {
  return TIME_FORMAT.format(new Date(ms));
}

/** Keeps the "agora" marker inside the viewport, near the right edge. */
const NOW_MARKER_INSET_PX = 40;

/**
 * Initial horizontal scroll so the visible window ends at the current instant.
 * A stop or production in progress finishes at "now", so that marker stays near
 * the right edge and the hours immediately before it stay on screen.
 */
export function timelineScrollLeftForNow(input: {
  nowMs: number;
  dayStartMs: number;
  daySpanMs: number;
  trackWidthPx: number;
  viewportWidthPx: number;
}): number {
  const { nowMs, dayStartMs, daySpanMs, trackWidthPx, viewportWidthPx } = input;
  const maxScroll = Math.max(0, trackWidthPx - viewportWidthPx);
  if (daySpanMs <= 0 || viewportWidthPx <= 0 || trackWidthPx <= 0) return 0;
  if (nowMs <= dayStartMs) return 0;
  if (nowMs >= dayStartMs + daySpanMs) return maxScroll;
  const nowPx = ((nowMs - dayStartMs) / daySpanMs) * trackWidthPx;
  return Math.min(maxScroll, Math.max(0, nowPx - viewportWidthPx + NOW_MARKER_INSET_PX));
}
