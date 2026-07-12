import type { NcBoardItem, NcDueSlaLevel } from "../types/ncManagement";

export type NcBoardRowStatusTone =
  | "pending"
  | "closed"
  | "overdue"
  | "on-track"
  | "ok";

export type NcBoardRowStatus = {
  label: string;
  tone: NcBoardRowStatusTone;
  hint?: string;
};

export function resolveNcBoardRowStatus(item: NcBoardItem): NcBoardRowStatus {
  if (item.is_registered === false || item.status === "pending") {
    return { label: "Aguardando registro", tone: "pending" };
  }
  if (item.status === "closed") {
    return { label: "Concluída", tone: "closed" };
  }
  if (item.due_sla_level === "overdue") {
    return {
      label: "Atrasado",
      tone: "overdue",
      hint: dueSlaHint(item.due_sla_level, item.days_until_due),
    };
  }
  if (item.due_sla_level === "due_soon") {
    return {
      label: "Em dia",
      tone: "on-track",
      hint: dueSlaHint(item.due_sla_level, item.days_until_due),
    };
  }
  if (item.due_sla_level === "ok") {
    return {
      label: "No prazo",
      tone: "ok",
      hint: dueSlaHint(item.due_sla_level, item.days_until_due),
    };
  }
  return { label: "Em dia", tone: "on-track" };
}

export function dueSlaLabel(level: NcDueSlaLevel): string {
  switch (level) {
    case "ok":
      return "No prazo";
    case "due_soon":
      return "Prazo próximo";
    case "overdue":
      return "Em atraso";
    default:
      return "Sem prazo";
  }
}

export function dueSlaHint(level: NcDueSlaLevel, daysUntilDue: number | null): string {
  if (level === "none" || daysUntilDue == null) {
    return "Defina um prazo para acompanhar o SLA.";
  }
  if (level === "overdue") {
    const days = Math.abs(daysUntilDue);
    return days === 1 ? "1 dia em atraso" : `${days} dias em atraso`;
  }
  if (level === "due_soon") {
    if (daysUntilDue === 0) return "Vence hoje";
    if (daysUntilDue === 1) return "Vence amanhã";
    return `Vence em ${daysUntilDue} dias`;
  }
  return `Faltam ${daysUntilDue} dias`;
}

export function workflowStepLabel(step: 1 | 2 | 3, planStarted: boolean): string {
  if (!planStarted) return "Não iniciado";
  switch (step) {
    case 1:
      return "Registrar plano";
    case 2:
      return "Anexar evidências";
    default:
      return "Finalizar ação";
  }
}
