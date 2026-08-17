import {
  statusBadgeBemClasses,
  type StatusBadgeVariant,
} from "@delpi/plugin-ui/index";

import { ATA_STATUS_LABELS } from "./meetingMinuteLabels";

export const tmAtaStatusBadgeClassNames = statusBadgeBemClasses("ds");

const STATUS_VARIANT: Record<string, StatusBadgeVariant> = {
  draft: "neutral",
  in_review: "info",
  awaiting_signatures: "warning",
  partially_signed: "warning",
  signed: "success",
  finalized: "success",
  cancelled: "danger",
};

export function ataStatusVariant(status: string): StatusBadgeVariant {
  return STATUS_VARIANT[status] ?? "neutral";
}

export function ataStatusLabel(status: string): string {
  return ATA_STATUS_LABELS[status] ?? status;
}

/** Data ISO (YYYY-MM-DD) → exibição pt-BR curta. */
export function formatAtaMeetingDate(value: string | undefined | null): string {
  const raw = String(value ?? "").trim();
  if (!raw) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(raw);
  if (!match) return raw;
  const [, y, m, d] = match;
  return `${d}/${m}/${y}`;
}

export function ataSignatureStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: "Pendente",
    viewed: "Visualizada",
    signed: "Assinada",
    refused: "Recusada",
    invalidated: "Invalidada",
    cancelled: "Cancelada",
  };
  return labels[status] ?? status;
}

export function ataSignatureProgress(item: {
  signatures_done?: number;
  signatures_pending?: number;
}): { done: number; total: number; label: string } {
  const done = item.signatures_done ?? 0;
  const pending = item.signatures_pending ?? 0;
  const total = done + pending;
  return {
    done,
    total,
    label: total > 0 ? `${done} de ${total} assinaturas` : "Sem signatários",
  };
}
