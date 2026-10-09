import type { ReactNode } from "react";

/**
 * Canonical presentation for Transformômetro statuses.
 * STATUS_PROCESSO (tm_app/core/catalogs.py): ativo | em_implantacao | descontinuado.
 * Every canonical value gets an explicit badge tone AND a human label —
 * no canonical status may render as a raw identifier.
 */
const STATUS_PRESENTATION: Record<string, { label: string; className: string }> = {
  ativo: { label: "Ativo", className: "ds-badge ds-badge--success" },
  em_implantacao: { label: "Em implantação", className: "ds-badge ds-badge--warning" },
  descontinuado: { label: "Descontinuado", className: "ds-badge ds-badge--info" },
};

function statusBadgeClass(value: string): string {
  const normalized = value.trim().toLowerCase();
  if (STATUS_PRESENTATION[normalized]) {
    return STATUS_PRESENTATION[normalized].className;
  }
  if (normalized === "aprovada" || normalized === "vigente") {
    return "ds-badge ds-badge--success";
  }
  if (
    normalized === "inativo" ||
    normalized === "encerrado" ||
    normalized === "rascunho" ||
    normalized === "cancelado"
  ) {
    return "ds-badge ds-badge--info";
  }
  if (normalized.includes("pendente") || normalized.includes("revis")) {
    return "ds-badge ds-badge--warning";
  }
  return "ds-badge";
}

function statusLabel(value: string): string {
  const normalized = value.trim().toLowerCase();
  const known = STATUS_PRESENTATION[normalized];
  if (known) return known.label;
  const humanized = normalized.replace(/_/g, " ");
  return humanized.charAt(0).toUpperCase() + humanized.slice(1);
}

export type StatusPresentation = { label: string; className: string };

export function statusPresentation(value: string): StatusPresentation {
  return { label: statusLabel(value), className: statusBadgeClass(value) };
}

export function renderTableStatus(value?: string | null): ReactNode {
  if (!value?.trim()) return "—";
  const { label, className } = statusPresentation(value);
  return <span className={className}>{label}</span>;
}
