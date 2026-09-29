import type { WorkCenterTimelineItem } from "../types/mes";

export type DayEventTone = "default" | "success" | "warning" | "danger" | "info";
export type DayEventPresentation = { label: string; tone: DayEventTone; pendingReason: boolean };

const TIME_FORMAT = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });

export function startOfLocalDayIso(now = new Date()): string {
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  return start.toISOString();
}

export function presentDayEvent(item: WorkCenterTimelineItem): DayEventPresentation {
  const pendingReason = Boolean(item.downtime && (!item.downtime.confirmed || !item.downtime.reasonCode));
  switch (item.state) {
    case "producing":
      return { label: "Produzindo", tone: "success", pendingReason };
    case "stopped":
      return { label: "Parada", tone: "danger", pendingReason };
    case "setup":
      return { label: "Setup", tone: "warning", pendingReason };
    case "planned_stop":
      return { label: "Parada planejada", tone: "info", pendingReason };
    case "idle":
      return { label: "Livre", tone: "default", pendingReason };
    default:
      return { label: "Estado indisponível", tone: "default", pendingReason };
  }
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
  return item.downtime?.reasonLabel ?? "Motivo não informado";
}
