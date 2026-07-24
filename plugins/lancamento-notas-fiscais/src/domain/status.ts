import type { AllowedAction, BlockReason, InvoicePostingStatus } from "./types";

export const STATUS_LABELS: Record<InvoicePostingStatus, string> = {
  pending: "Aguardando lançamento",
  in_progress: "Em atendimento",
  blocked: "Com pendência",
  posted: "Lançada",
  cancelled: "Cancelada",
};

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
