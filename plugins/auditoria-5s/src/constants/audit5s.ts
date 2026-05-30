export const API_BASE = "/apps/api-delpi/quality/audit-5s";

export const SHIFTS = [
  { value: "TURNO_1", label: "1º" },
  { value: "TURNO_2", label: "2º" },
  { value: "TURNO_3", label: "3º" },
  { value: "ADMINISTRATIVO", label: "Administrativo" },
] as const;

export const SCORE_OPTIONS = [
  { value: 1, label: "1 — Ruim" },
  { value: 3, label: "3 — Médio" },
  { value: 5, label: "5 — Bom" },
] as const;

/** Catálogo v1 — fallback quando o nome ainda não veio da API. */
export const SENSOS = [
  { order: 1, name: "Utilização" },
  { order: 2, name: "Ordenação" },
  { order: 3, name: "Limpeza" },
  { order: 4, name: "Padronização" },
  { order: 5, name: "Disciplina" },
] as const;

export function sensoName(order: number, nameFromApi?: string): string {
  if (nameFromApi?.trim()) {
    return nameFromApi.trim();
  }
  return SENSOS.find((item) => item.order === order)?.name ?? `Senso ${order}`;
}

export function branchFromPathname(pathname?: string): "01" | "02" | null {
  if (!pathname) return null;
  if (pathname.includes("filial-01")) return "01";
  if (pathname.includes("filial-02")) return "02";
  return null;
}

export function shiftLabel(value: string): string {
  return SHIFTS.find((item) => item.value === value)?.label ?? value;
}

const AUDIT_STATUS_LABELS: Record<string, string> = {
  draft: "Em avaliação",
  evaluation_complete: "Avaliação concluída",
  nc_in_progress: "NC em andamento",
  closed: "Encerrada",
};

const NC_STATUS_LABELS: Record<string, string> = {
  open: "Plano em registro",
  in_progress: "Aguardando evidências",
  closed: "Ação finalizada",
  cancelled: "Cancelada",
};

export function auditStatusLabel(value: string): string {
  return AUDIT_STATUS_LABELS[value] ?? value;
}

export function auditStatusVariant(value: string): "draft" | "complete" | "nc" | "closed" | "default" {
  switch (value) {
    case "draft":
      return "draft";
    case "evaluation_complete":
      return "complete";
    case "nc_in_progress":
      return "nc";
    case "closed":
      return "closed";
    default:
      return "default";
  }
}

export function ncStatusLabel(value: string): string {
  return NC_STATUS_LABELS[value] ?? value;
}

export function canAccessNc(status: string): boolean {
  return status === "evaluation_complete" || status === "nc_in_progress" || status === "closed";
}

export function ncActionLabel(status: string): string {
  switch (status) {
    case "evaluation_complete":
      return "Tratar NC";
    case "nc_in_progress":
      return "Continuar NC";
    case "closed":
      return "Ver NC";
    default:
      return "NC";
  }
}

export const NC_PRIORITY_OPTIONS = [
  { value: "high" as const, label: "Alta", tone: "high" },
  { value: "medium" as const, label: "Média", tone: "mid" },
  { value: "low" as const, label: "Baixa", tone: "low" },
];

export const NC_STATUS_OPTIONS = [
  { value: "open" as const, label: "Plano em registro", tone: "draft" },
  { value: "in_progress" as const, label: "Aguardando evidências", tone: "nc" },
  { value: "closed" as const, label: "Ação finalizada", tone: "closed" },
];

export function ncStatusVariant(value: string): "draft" | "nc" | "closed" | "default" {
  switch (value) {
    case "open":
      return "draft";
    case "in_progress":
      return "nc";
    case "closed":
      return "closed";
    default:
      return "default";
  }
}

export function ncPriorityLabel(value: string | null | undefined): string {
  return NC_PRIORITY_OPTIONS.find((item) => item.value === value)?.label ?? "—";
}

export function sensoAccentClass(order: number): string {
  return `a5s-nc-senso--${Math.min(Math.max(order, 1), 5)}`;
}
