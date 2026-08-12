import type { TimelineTone } from "@delpi/plugin-ui/index";

import type {
  SellerPortfolioAuditEvent,
  SellerPortfolioAuditTone,
} from "../types/portfolio";

export function formatPortfolioAuditWhen(iso?: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function toPortfolioAuditTimelineTone(
  tone: SellerPortfolioAuditTone | string | null | undefined,
): TimelineTone {
  switch (tone) {
    case "danger":
    case "warning":
    case "success":
    case "info":
      return tone;
    default:
      return "default";
  }
}

export type PortfolioAuditTimelineItem = {
  id: string;
  title: string;
  occurredAt: string | null;
  timeLabel: string;
  detail: string;
  tone: TimelineTone;
  actorUserId: string;
};

/** Ordena cronológico decrescente (API já entrega assim; reforça no cliente). */
export function mapPortfolioAuditEventsToTimelineItems(
  events: readonly SellerPortfolioAuditEvent[],
): PortfolioAuditTimelineItem[] {
  const sorted = [...events].sort((left, right) => {
    const a = left.created_at ? Date.parse(left.created_at) : 0;
    const b = right.created_at ? Date.parse(right.created_at) : 0;
    return b - a;
  });
  return sorted.map((event) => ({
    id: event.id,
    title: event.title || event.action,
    occurredAt: event.created_at,
    timeLabel: formatPortfolioAuditWhen(event.created_at),
    detail: event.message,
    tone: toPortfolioAuditTimelineTone(event.tone),
    actorUserId: event.actor_user_id,
  }));
}
