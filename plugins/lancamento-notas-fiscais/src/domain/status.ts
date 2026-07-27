import type { AllowedAction, BlockReason, InvoicePostingStatus } from "./types";

export const STATUS_LABELS: Record<InvoicePostingStatus, string> = {
  pending: "Aguardando lançamento",
  in_progress: "Em atendimento",
  blocked: "Com pendência",
  posted: "Lançada",
  cancelled: "Cancelada",
};

/** Tom visual compartilhado (badge + faixa lateral da fila). */
export const STATUS_TONES: Record<InvoicePostingStatus, string> = {
  pending: "pending",
  in_progress: "progress",
  blocked: "blocked",
  posted: "posted",
  cancelled: "cancelled",
};

/** Filtro de listagem: fila aberta (pending + in_progress + blocked). */
export const LIST_STATUS_FILTER_OPEN = "open";

export const STATUS_FILTER_OPTIONS: { value: string; label: string }[] = [
  {
    value: LIST_STATUS_FILTER_OPEN,
    label: "Em aberto",
  },
  ...Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label })),
];

export const BLOCK_REASON_LABELS: Record<BlockReason, string> = {
  purchase_order: "Aguardando pedido de compra",
  supplier_registration: "Aguardando cadastro de fornecedor",
  information_correction: "Aguardando correção de informações",
  other: "Outra pendência",
};

export const BLOCK_REASON_OPTIONS = (
  Object.keys(BLOCK_REASON_LABELS) as BlockReason[]
).map((value) => ({ value, label: BLOCK_REASON_LABELS[value] }));

export function statusLabel(status: string): string {
  return STATUS_LABELS[status as InvoicePostingStatus] ?? status;
}

export function statusTone(status: string): string {
  return STATUS_TONES[status as InvoicePostingStatus] ?? "pending";
}

export function blockReasonLabel(reason: string | null | undefined): string {
  if (!reason) return "—";
  return BLOCK_REASON_LABELS[reason as BlockReason] ?? reason;
}

export function hasAction(
  actions: AllowedAction[] | undefined,
  action: AllowedAction,
): boolean {
  return Boolean(actions?.includes(action));
}
