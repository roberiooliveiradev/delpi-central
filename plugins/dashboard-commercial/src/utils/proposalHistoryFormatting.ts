import type { CommercialProposalHistoryEvent } from "../types/commercial";

export function formatHistoryDate(value?: string | null): string {
  if (!value || value.length !== 8) return "—";

  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);

  return `${day}/${month}/${year}`;
}

export function formatHistoryDateTime(
  date?: string | null,
  time?: string | null
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
  label?: string | null
): string {
  const normalizedCode = code?.trim();
  const normalizedLabel = label?.trim();

  if (!normalizedCode && !normalizedLabel) return "—";
  if (normalizedLabel && normalizedCode && normalizedLabel !== normalizedCode) {
    if (!/^\d+$/.test(normalizedLabel)) {
      return normalizedLabel;
    }
    return `${normalizedLabel} (${normalizedCode})`;
  }

  return normalizedLabel || normalizedCode || "—";
}

export function resolveHistoryDuration(
  event: CommercialProposalHistoryEvent
): string {
  if (event.duration_display?.trim()) {
    return event.duration_display;
  }

  if (event.duration_minutes == null || Number.isNaN(event.duration_minutes)) {
    return "—";
  }

  return `${event.duration_minutes.toLocaleString("pt-BR")} min`;
}

export function resolveHistoryStatus(
  event: CommercialProposalHistoryEvent
): string {
  return event.status_label?.trim() || event.status?.trim() || "—";
}

export function isHistoryEngineeringFlow(
  event: CommercialProposalHistoryEvent
): boolean {
  return Boolean(event.is_engineering_flow ?? event.is_engineering);
}

export function resolveHistoryFlowLabels(
  event: CommercialProposalHistoryEvent
): string[] {
  if (event.flow_transition_labels && event.flow_transition_labels.length > 0) {
    return event.flow_transition_labels;
  }

  const labels: string[] = [];
  if (event.is_engineering_entry) {
    labels.push("Entrada na engenharia");
  }
  if (event.flow_transition_label) {
    labels.push(event.flow_transition_label);
  }
  return labels;
}

export type HistoryRevisionGroup = {
  revision: string;
  events: CommercialProposalHistoryEvent[];
};

export function groupHistoryByRevision(
  events: CommercialProposalHistoryEvent[]
): HistoryRevisionGroup[] {
  const groups = new Map<string, CommercialProposalHistoryEvent[]>();

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

export function buildHistoryEventKey(
  event: CommercialProposalHistoryEvent
): string {
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
