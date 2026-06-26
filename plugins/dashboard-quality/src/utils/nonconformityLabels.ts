import type { Nonconformity } from "../types/nonconformity";

const TYPE_LABELS_BY_CODE: Record<string, string> = {
  "1": "Interna",
  "2": "Cliente",
  "3": "Fornecedor",
};

const STATUS_LABELS_BY_CODE: Record<string, string> = {
  "1": "Registrada",
  "2": "Em análise",
  "3": "Procede",
  "4": "Não procede",
  "5": "Cancelada",
};

const LEGACY_TYPE_LABELS: Record<string, string> = {
  internal: "Interna",
  customer: "Cliente",
  supplier: "Fornecedor",
};

const LEGACY_STATUS_LABELS: Record<string, string> = {
  registered: "Registrada",
  under_analysis: "Em análise",
  proceeds: "Procede",
  does_not_proceed: "Não procede",
  cancelled: "Cancelada",
};

export function formatNonconformityTypeLabel(
  row: Pick<Nonconformity, "type_code" | "type_label">
): string {
  const code = row.type_code?.trim();
  if (code && TYPE_LABELS_BY_CODE[code]) {
    return TYPE_LABELS_BY_CODE[code];
  }

  const legacy = row.type_label?.trim().toLowerCase();
  if (legacy && LEGACY_TYPE_LABELS[legacy]) {
    return LEGACY_TYPE_LABELS[legacy];
  }

  return row.type_label?.trim() || code || "—";
}

export function formatNonconformityStatusLabel(
  row: Pick<Nonconformity, "status_code" | "status_label">
): string {
  const code = row.status_code?.trim();
  if (code && STATUS_LABELS_BY_CODE[code]) {
    return STATUS_LABELS_BY_CODE[code];
  }

  const legacy = row.status_label?.trim().toLowerCase();
  if (legacy && LEGACY_STATUS_LABELS[legacy]) {
    return LEGACY_STATUS_LABELS[legacy];
  }

  return row.status_label?.trim() || code || "—";
}
