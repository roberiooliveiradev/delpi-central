import type { LmpHistoryEvent } from "../types/lmp";

export function formatHistoryDate(value?: string | null): string {
  if (!value || value.length !== 8) return "—";

  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);

  return `${day}/${month}/${year}`;
}

export function formatHistoryDateTime(
  date?: string | null,
  time?: string | null,
): string {
  const formattedDate = formatHistoryDate(date);
  const normalizedTime = time?.trim();

  if (formattedDate === "—" && !normalizedTime) return "—";
  if (formattedDate === "—") return normalizedTime ?? "—";
  if (!normalizedTime) return formattedDate;

  return `${formattedDate} ${normalizedTime}`;
}

export function formatProcessStageLabel(
  code?: string | null,
  label?: string | null,
): string {
  const normalizedCode = code?.trim();
  const normalizedLabel = label?.trim();

  if (!normalizedCode && !normalizedLabel) return "—";
  if (normalizedLabel && normalizedCode && normalizedLabel !== normalizedCode) {
    return `${normalizedLabel} (${normalizedCode})`;
  }

  return normalizedLabel || normalizedCode || "—";
}

export function resolveHistoryDuration(event: LmpHistoryEvent): string {
  if (event.duration_display?.trim()) {
    return event.duration_display;
  }

  if (event.duration_minutes == null || Number.isNaN(event.duration_minutes)) {
    return "—";
  }

  return `${event.duration_minutes.toLocaleString("pt-BR")} min`;
}

export function resolveHistoryStatus(event: LmpHistoryEvent): string {
  return event.status_label?.trim() || event.status?.trim() || "—";
}

export function isHistoryEngineeringFlow(event: LmpHistoryEvent): boolean {
  return Boolean(event.is_engineering_flow ?? event.is_engineering);
}

export function buildHistoryEventKey(event: LmpHistoryEvent): string {
  return [
    event.revision,
    event.process_code,
    event.stage_code,
    event.start_date,
    event.start_time,
    event.end_date,
    event.end_time,
  ].join("-");
}

export type HistoryRevisionGroup = {
  revision: string;
  events: LmpHistoryEvent[];
};

export type HistoryEventFilter = "all" | "engineering" | "open" | "current_revision";

export function resolveCurrentRevision(events: LmpHistoryEvent[]): string | null {
  const currentEvent = events.find((event) => event.is_current);
  if (currentEvent?.revision?.trim()) {
    return currentEvent.revision.trim();
  }

  if (events.length === 0) {
    return null;
  }

  return events[events.length - 1]?.revision?.trim() || null;
}

export function filterHistoryEvents(
  events: LmpHistoryEvent[],
  filter: HistoryEventFilter,
): LmpHistoryEvent[] {
  if (filter === "all") {
    return events;
  }

  if (filter === "engineering") {
    return events.filter((event) => isHistoryEngineeringFlow(event));
  }

  if (filter === "open") {
    return events.filter((event) => Boolean(event.is_open));
  }

  const currentRevision = resolveCurrentRevision(events);
  if (!currentRevision) {
    return events;
  }

  return events.filter((event) => (event.revision?.trim() || "—") === currentRevision);
}

export function groupHistoryByRevision(events: LmpHistoryEvent[]): HistoryRevisionGroup[] {
  const groups = new Map<string, LmpHistoryEvent[]>();

  for (const event of events) {
    const revision = event.revision?.trim() || "—";
    const bucket = groups.get(revision) ?? [];
    bucket.push(event);
    groups.set(revision, bucket);
  }

  return Array.from(groups.entries()).map(([revision, revisionEvents]) => ({
    revision,
    events: revisionEvents,
  }));
}

export function summarizeHistoryEvents(
  events: LmpHistoryEvent[],
  options?: { totalCount?: number },
): string {
  const totalCount = options?.totalCount ?? events.length;
  const openCount = events.filter((event) => event.is_open).length;
  const revisionCount = new Set(events.map((event) => event.revision)).size;

  if (events.length === 0) {
    return totalCount > 0
      ? `Nenhum evento no filtro (${totalCount} no total)`
      : "Nenhum evento registrado";
  }

  const parts = [
    totalCount !== events.length
      ? `${events.length} de ${totalCount} evento(s)`
      : `${events.length} evento(s)`,
    `${revisionCount} revisão(ões)`,
  ];

  if (openCount > 0) {
    parts.push(`${openCount} em aberto`);
  }

  return parts.join(" · ");
}
