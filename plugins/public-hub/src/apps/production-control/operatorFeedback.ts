import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime.ts";
import type { OperatorFeedbackStatus, PublicOperatorFeedback } from "./api.ts";
import type { OperatorSessionStatus } from "./OperatorSessionContext.ts";

/**
 * Catálogo e apresentação do Operator Feedback (C3).
 *
 * Domínio próprio: missing_material aqui NÃO é motivo de parada MES — os
 * códigos/labels vivem neste módulo para crescer sem espalhar strings.
 */

export const OPERATOR_FEEDBACK_TYPES = [
  { code: "cannot_produce", label: "Não será possível produzir" },
] as const;

export const OPERATOR_FEEDBACK_REASONS = [
  { code: "missing_material", label: "Falta de matéria-prima" },
] as const;

export const DEFAULT_FEEDBACK_TYPE = OPERATOR_FEEDBACK_TYPES[0].code;
export const DEFAULT_FEEDBACK_REASON = OPERATOR_FEEDBACK_REASONS[0].code;
export const FEEDBACK_NOTE_MAX_LENGTH = 500;

export type FeedbackStatusTone = "informed" | "treating" | "muted";

export type FeedbackStatusPresentation = {
  label: string;
  hint: string;
  tone: FeedbackStatusTone;
};

const STATUS_PRESENTATION: Record<
  OperatorFeedbackStatus,
  FeedbackStatusPresentation
> = {
  open: {
    label: "PCP informado",
    hint: "O PCP recebeu o aviso e ainda não iniciou a tratativa.",
    tone: "informed",
  },
  acknowledged: {
    label: "PCP em tratativa",
    hint: "O PCP já visualizou o impedimento e está tratando a situação.",
    tone: "treating",
  },
  resolved: {
    label: "Impedimento resolvido",
    hint: "O PCP resolveu este impedimento.",
    tone: "muted",
  },
};

/** Status → linguagem do operador; desconhecido cai num fallback seguro. */
export function feedbackStatusPresentation(
  status: string | null | undefined,
): FeedbackStatusPresentation {
  if (status === "open" || status === "acknowledged" || status === "resolved") {
    return STATUS_PRESENTATION[status];
  }
  return {
    label: "Aviso registrado",
    hint: "O PCP recebeu um aviso sobre esta operação.",
    tone: "muted",
  };
}

export function feedbackTypeLabel(code: string | null | undefined): string {
  const found = OPERATOR_FEEDBACK_TYPES.find((item) => item.code === code);
  return found?.label ?? "Impedimento informado";
}

export function feedbackReasonLabel(code: string | null | undefined): string {
  const found = OPERATOR_FEEDBACK_REASONS.find((item) => item.code === code);
  return found?.label ?? "Motivo informado ao PCP";
}

/** Impedimento ativo da operação (open|acknowledged); resolved nunca volta. */
export function firstActiveFeedback(
  items: PublicOperatorFeedback[] | null | undefined,
): PublicOperatorFeedback | null {
  if (!items?.length) return null;
  return (
    items.find((item) => item.status === "open" || item.status === "acknowledged") ??
    null
  );
}

/** O hint realtime só interessa se for exatamente da OP/operação aberta. */
export function isFeedbackEventForOperation(
  event: MachineLoadRealtimeEvent | null | undefined,
  productionOrder: string,
  operationCode: string,
): boolean {
  if (!event || event.type !== "operator_feedback_updated") return false;
  const order = String(productionOrder || "").trim().toUpperCase();
  const eventOrder = String(event.productionOrder || "").trim().toUpperCase();
  const op = String(operationCode || "").trim().replace(/^0+/, "") || "0";
  const eventOp =
    String(event.operationCode || "").trim().replace(/^0+/, "") || "0";
  return Boolean(order) && order === eventOrder && op === eventOp;
}

export type FeedbackPanelState =
  | "restoring"
  | "anonymous"
  | "loading"
  | "error"
  | "none"
  | "open"
  | "acknowledged";

/** Máquina de estados da seção — pura e testável sem React. */
export function resolveFeedbackPanelState(options: {
  sessionStatus: OperatorSessionStatus;
  loading: boolean;
  error: string | null;
  active: PublicOperatorFeedback | null;
}): FeedbackPanelState {
  if (options.sessionStatus === "restoring") return "restoring";
  if (options.sessionStatus !== "identified") return "anonymous";
  if (options.loading && !options.active) return "loading";
  if (options.error && !options.active) return "error";
  const status = options.active?.status;
  if (status === "open") return "open";
  if (status === "acknowledged") return "acknowledged";
  return "none";
}

/** Mensagem amigável para o POST falhar — nunca vaza detalhe interno. */
export function feedbackSubmitErrorMessage(status: number | null): string {
  if (status === 409) {
    return "O PCP já foi informado sobre este impedimento.";
  }
  if (status === 404) {
    return "Esta operação não está mais disponível neste posto. Atualize a fila.";
  }
  if (status === 401) {
    return "Sua identificação expirou. Identifique-se novamente.";
  }
  return "Não foi possível enviar o aviso ao PCP. Tente novamente.";
}
