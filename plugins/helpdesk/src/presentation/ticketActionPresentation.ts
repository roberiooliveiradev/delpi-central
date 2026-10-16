import type { LucideIcon } from "lucide-react";
import {
  BadgeCheck,
  CheckCircle2,
  ClipboardCheck,
  MessageSquare,
  Paperclip,
  Star,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";

import type { TicketWorkspaceActionId } from "./ticketWorkspaceActions";

/** Semantic visual variants — CSS `data-action-variant`. Color never sole signal. */
export type TicketActionVariant =
  | "reply"
  | "solution"
  | "task"
  | "attachment"
  | "approval"
  | "validation"
  | "satisfaction"
  | "accept"
  | "reject";

export type TicketActionPresentation = {
  id: TicketWorkspaceActionId;
  variant: TicketActionVariant;
  icon: LucideIcon;
  label: string;
  submitLabel: string;
  submittingLabel: string;
  helperText: string;
  errorFallback: string;
  successLabel: string;
};

const PRESENTATION: Record<TicketWorkspaceActionId, TicketActionPresentation> = {
  reply: {
    id: "reply",
    variant: "reply",
    icon: MessageSquare,
    label: "Responder",
    submitLabel: "Enviar resposta",
    submittingLabel: "Enviando…",
    helperText: "Envie uma resposta neste chamado.",
    errorFallback: "Não foi possível enviar a resposta.",
    successLabel: "Resposta enviada.",
  },
  create_solution: {
    id: "create_solution",
    variant: "solution",
    icon: CheckCircle2,
    label: "Adicionar solução",
    submitLabel: "Adicionar solução",
    submittingLabel: "Adicionando solução…",
    helperText: "Registre a solução deste chamado.",
    errorFallback: "Não foi possível adicionar a solução.",
    successLabel: "Solução adicionada.",
  },
  create_task: {
    id: "create_task",
    variant: "task",
    icon: ClipboardCheck,
    label: "Criar tarefa",
    submitLabel: "Criar tarefa",
    submittingLabel: "Criando tarefa…",
    helperText: "Crie uma tarefa vinculada a este chamado.",
    errorFallback: "Não foi possível criar a tarefa.",
    successLabel: "Tarefa criada.",
  },
  attach_file: {
    id: "attach_file",
    variant: "attachment",
    icon: Paperclip,
    label: "Anexar arquivo",
    submitLabel: "Anexar arquivo",
    submittingLabel: "Anexando…",
    helperText: "Anexe arquivos ao chamado sem enviar uma mensagem.",
    errorFallback: "Não foi possível anexar o arquivo.",
    successLabel: "Arquivo anexado.",
  },
  request_approval: {
    id: "request_approval",
    variant: "approval",
    icon: ThumbsUp,
    label: "Pedir aprovação",
    submitLabel: "Pedir aprovação",
    submittingLabel: "Solicitando aprovação…",
    helperText: "Solicite a aprovação deste chamado a um usuário ou grupo.",
    errorFallback: "Não foi possível solicitar a aprovação.",
    successLabel: "Aprovação solicitada.",
  },
  accept_solution: {
    id: "accept_solution",
    variant: "accept",
    icon: ThumbsUp,
    label: "Aceitar solução",
    submitLabel: "Aceitar solução",
    submittingLabel: "Aceitando…",
    helperText: "Fecha o chamado após aceitar a solução.",
    errorFallback: "Não foi possível aceitar a solução.",
    successLabel: "Solução aceita.",
  },
  reject_solution: {
    id: "reject_solution",
    variant: "reject",
    icon: ThumbsDown,
    label: "Recusar / reabrir",
    submitLabel: "Recusar / reabrir",
    submittingLabel: "Recusando…",
    helperText: "Recusa a solução e reabre o atendimento.",
    errorFallback: "Não foi possível recusar a solução.",
    successLabel: "Solução recusada.",
  },
  decide_validation: {
    id: "decide_validation",
    variant: "validation",
    icon: BadgeCheck,
    label: "Decidir aprovação",
    submitLabel: "Registrar decisão",
    submittingLabel: "Registrando…",
    helperText: "Aceite ou recuse a aprovação pendente atribuída a você.",
    errorFallback: "Não foi possível registrar a decisão.",
    successLabel: "Decisão registrada.",
  },
  submit_satisfaction: {
    id: "submit_satisfaction",
    variant: "satisfaction",
    icon: Star,
    label: "Avaliar atendimento",
    submitLabel: "Enviar avaliação",
    submittingLabel: "Enviando…",
    helperText: "Avalie o atendimento deste chamado de 1 a 5.",
    errorFallback: "Não foi possível enviar a avaliação.",
    successLabel: "Avaliação registrada.",
  },
};

export function ticketActionPresentation(
  id: TicketWorkspaceActionId,
): TicketActionPresentation {
  return PRESENTATION[id];
}

/**
 * Selector order — pending lifecycle decisions first so the requester sees
 * accept/reject at the top of the single action menu.
 */
export const SELECTOR_ACTION_IDS: readonly TicketWorkspaceActionId[] = [
  "accept_solution",
  "reject_solution",
  "decide_validation",
  "submit_satisfaction",
  "reply",
  "create_solution",
  "create_task",
  "attach_file",
  "request_approval",
] as const;

/** Action ids that represent a pending requester decision. */
export const PENDING_DECISION_ACTION_IDS: readonly TicketWorkspaceActionId[] = [
  "accept_solution",
  "reject_solution",
  "decide_validation",
] as const;
