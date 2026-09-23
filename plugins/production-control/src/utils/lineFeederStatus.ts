import type { LineFeederItemStatus, LineFeederStatus } from "../types";

type BadgeVariant = "neutral" | "info" | "success" | "warning" | "danger";

const REQUIREMENT_VARIANTS: Record<LineFeederStatus, BadgeVariant> = {
  covered: "success",
  to_pick: "warning",
  at_risk: "danger",
  unknown: "neutral",
};

const ITEM_VARIANTS: Record<LineFeederItemStatus, BadgeVariant> = {
  pending: "warning",
  picked: "info",
  delivered: "success",
};

export function requirementBadgeVariant(status: string): BadgeVariant {
  return REQUIREMENT_VARIANTS[status as LineFeederStatus] ?? "neutral";
}

export function pickItemBadgeVariant(status: string): BadgeVariant {
  return ITEM_VARIANTS[status as LineFeederItemStatus] ?? "neutral";
}

/** Próximo passo do item na coleta; entregue volta para a coleta (o toque erra). */
export function nextPickItemStatus(status: string): LineFeederItemStatus {
  if (status === "pending") return "picked";
  if (status === "picked") return "delivered";
  return "pending";
}

/** «14:30» a partir do ISO do BFF; sem data válida não inventa horário. */
export function formatScheduleTime(value: string | null): string {
  if (!value) return "—";
  const match = /T(\d{2}):(\d{2})/.exec(value);
  if (!match) return "—";
  return `${match[1]}:${match[2]}`;
}
