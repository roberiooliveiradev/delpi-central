import type { LucideIcon } from "lucide-react";
import {
  CheckCircle2,
  ClipboardCheck,
  MessageSquare,
  Paperclip,
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
    helperText: "Acompanhamento público no chamado.",
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
    helperText: "Registra a solução pública do chamado (status depende do helpdesk).",
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
    helperText: "Tarefa pública visível na conversa.",
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
    helperText: "Anexa arquivos ao chamado sem enviar mensagem.",
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
    helperText: "Designa um aprovador e envia o pedido de validação.",
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
};

export function ticketActionPresentation(
  id: TicketWorkspaceActionId,
): TicketActionPresentation {
  return PRESENTATION[id];
}

/** Actions shown in the bottom selector (not contextual lifecycle). */
export const SELECTOR_ACTION_IDS: readonly TicketWorkspaceActionId[] = [
  "reply",
  "create_solution",
  "create_task",
  "attach_file",
  "request_approval",
] as const;
