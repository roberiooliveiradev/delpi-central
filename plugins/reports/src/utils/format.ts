/** Rótulos de filial — alinhados ao e-mail / inspeções. */
export const BRANCH_UNIT_LABELS: Record<string, string> = {
  "01": "Jaraguá do Sul/SC",
  "02": "Rio Bananal/ES",
};

export function formatBranchUnitLabel(branch: string | null | undefined): string {
  const code = String(branch ?? "").trim();
  if (!code) return "—";
  return BRANCH_UNIT_LABELS[code] ?? `Filial ${code}`;
}

export function formatDateTimeBr(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTriggerLabel(trigger: string): string {
  switch (trigger) {
    case "manual":
      return "Manual";
    case "schedule":
      return "Agenda";
    case "event":
      return "Evento";
    default:
      return trigger || "—";
  }
}

export function formatRunStatusLabel(status: string): string {
  switch (status) {
    case "succeeded":
      return "Sucesso";
    case "failed":
      return "Falhou";
    case "running":
      return "Em execução";
    case "pending":
      return "Pendente";
    default:
      return status || "—";
  }
}
