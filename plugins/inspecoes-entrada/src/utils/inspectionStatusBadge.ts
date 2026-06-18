import type { ResultBadgeDescriptor } from "./resultBadge";

const STATUS_LABELS: Record<string, string> = {
  NAO_IDENTIFICADA: "Não identificada",
  PENDENTE_LAUDO_GERAL: "Pendente laudo",
  PENDENTE: "Pendente",
};

export function resolveInspectionStatusBadge(status: string): ResultBadgeDescriptor {
  const normalized = status.trim().toUpperCase();

  if (!normalized) {
    return { label: "—", tone: "neutral" };
  }

  const label = STATUS_LABELS[normalized] ?? status.trim().replaceAll("_", " ");

  if (normalized.includes("PENDENTE") || normalized === "NAO_IDENTIFICADA") {
    return { label, tone: "warning" };
  }

  if (normalized.includes("REJEIT")) {
    return { label, tone: "danger" };
  }

  if (normalized.includes("APROV")) {
    return { label, tone: "success" };
  }

  return { label, tone: "neutral" };
}
