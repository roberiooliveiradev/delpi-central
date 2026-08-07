import type { CommercialProposalHistoryEvent } from "../types/analytics";
import type { OpTimelineItem, OpTimelineTone } from "./opTimeline";
import { formatDisplayDate } from "./dates";

export function formatProcessStageLabel(
  code?: string | null,
  label?: string | null,
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

export function resolveHistoryDuration(event: CommercialProposalHistoryEvent): string {
  if (event.duration_display?.trim()) {
    return event.duration_display;
  }
  if (event.duration_minutes == null || Number.isNaN(event.duration_minutes)) {
    return "—";
  }
  return `${event.duration_minutes.toLocaleString("pt-BR")} min`;
}

export function resolveHistoryStatus(event: CommercialProposalHistoryEvent): string {
  return event.status_label?.trim() || event.status?.trim() || "—";
}

export function historyEventKey(event: CommercialProposalHistoryEvent, index: number): string {
  return [
    event.revision,
    event.process_code,
    event.stage_code,
    event.start_date,
    event.end_date,
    String(index),
  ].join("-");
}

function historyTone(event: CommercialProposalHistoryEvent): OpTimelineTone {
  if (event.is_late) return "danger";
  if (event.is_open) return "info";
  if (event.is_current) return "success";
  return "default";
}

/** Converte eventos AIJ010 em itens do Timeline do kit. */
export function mapProposalHistoryToTimelineItems(
  events: CommercialProposalHistoryEvent[],
): OpTimelineItem[] {
  return events.map((event, index) => {
    const stage = formatProcessStageLabel(event.stage_code, event.stage_label);
    const process = formatProcessStageLabel(event.process_code, event.process_label);
    const badges: string[] = [];
    if (event.is_current) badges.push(event.is_open ? "Atual" : "Último");
    if (event.is_open) badges.push("Em andamento");
    else badges.push("Concluído");
    if (event.is_late) badges.push("Atrasado");
    if (event.is_engineering_flow || event.is_engineering) badges.push("Engenharia");

    return {
      id: historyEventKey(event, index),
      title: stage,
      occurredAt: event.start_date || event.end_date || null,
      timeLabel: formatDisplayDate(event.start_date || event.end_date),
      detail: [process, resolveHistoryStatus(event), badges.join(" · ")]
        .filter(Boolean)
        .join(" — "),
      tone: historyTone(event),
    };
  });
}
