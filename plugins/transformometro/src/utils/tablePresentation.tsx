import type { ReactNode } from "react";

function statusBadgeClass(value: string): string {
  const normalized = value.trim().toLowerCase();
  if (normalized === "ativo" || normalized === "aprovada" || normalized === "vigente") {
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

export function renderTableStatus(value?: string | null): ReactNode {
  if (!value?.trim()) return "—";
  return <span className={statusBadgeClass(value)}>{value.trim()}</span>;
}
