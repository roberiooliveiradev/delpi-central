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
