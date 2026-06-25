import {
  actionTypeLabel,
  EFFECTIVENESS_STATUSES,
  statusLabel,
} from "../constants/actionPlans";
import type { ActionPlanDetail, PlanHistoryEvent } from "../types/actionPlan";
import type { PlanEvidence } from "../types/rnc8d";

export type TimelineCategory = "status" | "actions" | "evidence" | "effectiveness" | "analysis";

export type TimelineFilter = "all" | TimelineCategory;

export type PlanTimelineEntry = {
  id: string;
  category: TimelineCategory;
  title: string;
  detail?: string;
  meta?: string;
  occurredAt: string;
};

const EFFECTIVENESS_LABELS = Object.fromEntries(
  EFFECTIVENESS_STATUSES.map((item) => [item.value, item.label]),
) as Record<string, string>;

function parseTime(value?: string | null): number {
  if (!value) return 0;
  const time = Date.parse(value);
  return Number.isNaN(time) ? 0 : time;
}

function effectivenessLabel(value?: string | null): string {
  if (!value) return "—";
  return EFFECTIVENESS_LABELS[value] ?? value;
}

function categoryForEventType(eventType: string): TimelineCategory {
  if (eventType === "effectiveness_reviewed") return "effectiveness";
  if (eventType.startsWith("action_")) return "actions";
  if (eventType === "evidence_uploaded") return "evidence";
  if (eventType === "ishikawa_updated" || eventType === "five_whys_updated") return "analysis";
  return "status";
}

function titleForHistoryEvent(event: PlanHistoryEvent): string {
  switch (event.event_type) {
    case "plan_created":
      return "Plano criado";
    case "plan_updated":
      return "Identificação atualizada";
    case "status_changed":
      return event.old_value && event.new_value
        ? `Status: ${statusLabel(event.old_value)} → ${statusLabel(event.new_value)}`
        : "Status atualizado";
    case "action_created":
      return "Ação registrada";
    case "action_completed":
      return "Ação concluída";
    case "action_updated":
      return "Ação atualizada";
    case "effectiveness_reviewed":
      return `Eficácia: ${effectivenessLabel(event.new_value)}`;
    case "ishikawa_updated":
      return "Ishikawa atualizado";
    case "five_whys_updated":
      return "5 Porquês atualizado";
    default:
      return event.event_type.replace(/_/g, " ");
  }
}

function entryFromHistory(event: PlanHistoryEvent): PlanTimelineEntry | null {
  const occurredAt = event.created_at;
  if (!occurredAt) return null;

  const detail =
    event.event_type === "action_created" && event.new_value
      ? event.new_value
      : event.comment?.trim() || undefined;

  return {
    id: `history-${event.id}`,
    category: categoryForEventType(event.event_type),
    title: titleForHistoryEvent(event),
    detail,
    meta: event.created_by ? `Por ${event.created_by}` : undefined,
    occurredAt,
  };
}

function entryFromEvidence(evidence: PlanEvidence): PlanTimelineEntry | null {
  if (!evidence.created_at) return null;

  const label = evidence.file_name || evidence.description || evidence.type || "Arquivo";
  const actionHint = evidence.action_id ? " · vinculada a ação" : "";

  return {
    id: `evidence-${evidence.id}`,
    category: "evidence",
    title: "Evidência anexada",
    detail: label,
    meta: evidence.uploaded_by
      ? `Por ${evidence.uploaded_by}${actionHint}`
      : actionHint || undefined,
    occurredAt: evidence.created_at,
  };
}

function entryFromPlanCreated(detail: ActionPlanDetail): PlanTimelineEntry | null {
  const occurredAt = detail.plan.created_at;
  if (!occurredAt) return null;

  return {
    id: `plan-created-${detail.plan.id}`,
    category: "status",
    title: "Plano criado",
    detail: detail.plan.code ? `Código ${detail.plan.code}` : undefined,
    occurredAt,
  };
}

export function buildPlanTimeline(detail: ActionPlanDetail): PlanTimelineEntry[] {
  const entries: PlanTimelineEntry[] = [];
  const seen = new Set<string>();

  for (const event of detail.history) {
    const entry = entryFromHistory(event);
    if (!entry) continue;
    entries.push(entry);
    seen.add(entry.id);
  }

  const hasPlanCreated = detail.history.some((event) => event.event_type === "plan_created");
  if (!hasPlanCreated) {
    const created = entryFromPlanCreated(detail);
    if (created && !seen.has(created.id)) {
      entries.push(created);
      seen.add(created.id);
    }
  }

  for (const evidence of detail.evidences ?? []) {
    const entry = entryFromEvidence(evidence);
    if (!entry || seen.has(entry.id)) continue;
    entries.push(entry);
    seen.add(entry.id);
  }

  for (const action of detail.actions) {
    const actionRecord = action as typeof action & {
      created_at?: string;
      completed_at?: string;
    };
    if (actionRecord.completed_at) {
      const id = `action-completed-${action.id}`;
      if (!seen.has(id)) {
        entries.push({
          id,
          category: "actions",
          title: "Ação concluída",
          detail: `${actionTypeLabel(action.action_type)} · ${action.description}`,
          occurredAt: actionRecord.completed_at,
        });
        seen.add(id);
      }
    }
  }

  return entries.sort((left, right) => parseTime(left.occurredAt) - parseTime(right.occurredAt));
}

export function filterTimelineEntries(
  entries: PlanTimelineEntry[],
  filter: TimelineFilter,
): PlanTimelineEntry[] {
  if (filter === "all") return entries;
  return entries.filter((entry) => entry.category === filter);
}

export const TIMELINE_FILTER_OPTIONS: Array<{ value: TimelineFilter; label: string }> = [
  { value: "all", label: "Todos" },
  { value: "status", label: "Status" },
  { value: "actions", label: "Ações" },
  { value: "evidence", label: "Evidências" },
  { value: "effectiveness", label: "Eficácia" },
];
