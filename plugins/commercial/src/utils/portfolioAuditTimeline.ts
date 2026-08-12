import type { TimelineTone } from "@delpi/plugin-ui/index";

import {
  PORTFOLIO_AUDIT_CONTENT,
  type PortfolioAuditEventFilter,
} from "../content/portfolioAuditContent";
import type {
  SellerPortfolioAuditEvent,
  SellerPortfolioAuditTone,
} from "../types/portfolio";

const UUID_RE =
  /[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/gi;

const CUSTOMER_ACTIONS = new Set([
  "seller_portfolio.add_customer",
  "seller_portfolio.remove_customer",
  "seller_portfolio.replace_customers",
]);

const MEMBER_ACTIONS = new Set([
  "seller_portfolio.add_member",
  "seller_portfolio.remove_member",
  "seller_portfolio.replace_members",
  "seller_portfolio.set_owner",
  "seller_portfolio.create",
  "seller_portfolio.rename",
]);

const STATUS_ACTIONS = new Set([
  "seller_portfolio.deactivate",
  "seller_portfolio.reactivate",
  "seller_portfolio.purge",
]);

const TRANSFER_ACTIONS = new Set([
  "seller_portfolio.transfer_customers",
  "seller_portfolio.transfer_customers_bulk",
]);

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

export function portfolioAuditEventFilterCategory(
  action: string | null | undefined,
): Exclude<PortfolioAuditEventFilter, "all"> {
  const key = (action || "").trim();
  if (CUSTOMER_ACTIONS.has(key)) return "customers";
  if (MEMBER_ACTIONS.has(key)) return "members";
  if (STATUS_ACTIONS.has(key)) return "status";
  if (TRANSFER_ACTIONS.has(key)) return "transfers";
  return "members";
}

export function filterPortfolioAuditEvents(
  events: readonly SellerPortfolioAuditEvent[],
  filter: PortfolioAuditEventFilter,
): SellerPortfolioAuditEvent[] {
  if (filter === "all") return [...events];
  return events.filter(
    (event) => portfolioAuditEventFilterCategory(event.action) === filter,
  );
}

function payloadString(
  payload: Record<string, unknown> | null | undefined,
  key: string,
): string {
  const value = payload?.[key];
  return typeof value === "string" ? value.trim() : "";
}

/**
 * Troca UUID / rótulo genérico por nome do diretório; remove IDs técnicos restantes.
 */
export function humanizePortfolioAuditMessage(
  event: SellerPortfolioAuditEvent,
  directoryLabelFor: (userId: string, fallback?: string | null) => string,
): string {
  let message = (event.message || "").trim();
  if (!message) return message;

  const payload = (event.payload || {}) as Record<string, unknown>;
  const subjectId = payloadString(payload, "user_id");
  if (subjectId) {
    const label = directoryLabelFor(subjectId, PORTFOLIO_AUDIT_CONTENT.anonymousUser);
    if (label && label !== subjectId) {
      message = message.split(subjectId).join(label);
      if (message.includes(PORTFOLIO_AUDIT_CONTENT.anonymousUser)) {
        message = message.replace(
          PORTFOLIO_AUDIT_CONTENT.anonymousUser,
          label,
        );
      }
    }
  }

  message = message.replace(UUID_RE, (match) => {
    const label = directoryLabelFor(match, "");
    if (label && label !== match && label !== "Usuário") return label;
    return PORTFOLIO_AUDIT_CONTENT.anonymousUser;
  });

  return message;
}

export type PortfolioAuditTimelineItem = {
  id: string;
  title: string;
  occurredAt: string | null;
  timeLabel: string;
  detail: string;
  tone: TimelineTone;
  actorUserId: string;
  filterCategory: Exclude<PortfolioAuditEventFilter, "all">;
};

/** Ordena cronológico decrescente (API já entrega assim; reforça no cliente). */
export function mapPortfolioAuditEventsToTimelineItems(
  events: readonly SellerPortfolioAuditEvent[],
  directoryLabelFor?: (userId: string, fallback?: string | null) => string,
): PortfolioAuditTimelineItem[] {
  const labelFor =
    directoryLabelFor ||
    ((id: string, fallback?: string | null) => fallback || id);
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
    detail: humanizePortfolioAuditMessage(event, labelFor),
    tone: toPortfolioAuditTimelineTone(event.tone),
    actorUserId: event.actor_user_id,
    filterCategory: portfolioAuditEventFilterCategory(event.action),
  }));
}
