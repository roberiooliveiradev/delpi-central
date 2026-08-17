import type { AllowedAction, FreightMode, InvoiceType, IssuanceStatus, PartyType } from "./types";

export const STATUS_LABELS: Record<IssuanceStatus, string> = {
  pending: "Aguardando atendimento",
  in_progress: "Em atendimento",
  issued: "Emitida",
  returned: "Devolvida para correção",
  cancelled: "Cancelada",
};

export const STATUS_TONES: Record<IssuanceStatus, string> = {
  pending: "pending",
  in_progress: "progress",
  issued: "posted",
  returned: "blocked",
  cancelled: "cancelled",
};

export const LIST_STATUS_FILTER_OPEN = "open";

export const STATUS_FILTER_OPTIONS: { value: string; label: string }[] = [
  { value: LIST_STATUS_FILTER_OPEN, label: "Em aberto" },
  ...Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label })),
];

export const INVOICE_TYPE_LABELS: Record<InvoiceType, string> = {
  sale: "Venda",
  return: "Devolução",
  sample: "Amostra",
  repair_shipment: "Remessa ou retorno de conserto",
  other: "Outros",
};

export const PARTY_TYPE_LABELS: Record<PartyType, string> = {
  customer: "Cliente",
  supplier: "Fornecedor",
};

export const FREIGHT_MODE_LABELS: Record<FreightMode, string> = {
  cif: "CIF",
  fob: "FOB",
};

export function statusLabel(status: string): string {
  return STATUS_LABELS[status as IssuanceStatus] ?? status;
}

export function statusTone(status: string): string {
  return STATUS_TONES[status as IssuanceStatus] ?? "pending";
}

export const EVENT_TYPE_LABELS: Record<string, string> = {
  created: "Solicitação criada",
  updated: "Dados atualizados",
  resubmitted: "Reenviada",
  started: "Atendimento iniciado",
  returned: "Devolvida",
  issued: "Emitida",
  cancelled: "Cancelada",
};

export function invoiceTypeLabel(value: string): string {
  return INVOICE_TYPE_LABELS[value as InvoiceType] ?? value;
}

export function partyTypeLabel(value: string): string {
  return PARTY_TYPE_LABELS[value as PartyType] ?? value;
}

export function freightModeLabel(value: string): string {
  return FREIGHT_MODE_LABELS[value as FreightMode] ?? value.toUpperCase();
}

export function historyEventLabel(eventType: string): string {
  return EVENT_TYPE_LABELS[eventType] ?? eventType;
}

export function hasAction(
  actions: AllowedAction[] | undefined,
  action: AllowedAction,
): boolean {
  return Boolean(actions?.includes(action));
}
