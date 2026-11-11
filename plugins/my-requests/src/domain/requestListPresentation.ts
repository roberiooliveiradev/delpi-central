import { parseGeneralRequestPayload } from "../features/general-request/domain/generalRequestPayload";
import { parseProcessIssuePayload } from "../features/process-issue/domain/processIssuePayload";
import type { RequestSummary } from "../types/requests";

/**
 * Título/assunto legível para listas (mine / work-queue).
 * Usa campos do payload já retornados pela API — sem fetch extra.
 */
export function requestListTitle(row: RequestSummary): string | null {
  const payload = row.payload;
  if (!payload || typeof payload !== "object") return null;

  switch (row.type_code) {
    case "general-request": {
      return parseGeneralRequestPayload(payload).title;
    }
    case "invoice-issuance": {
      const name = String(payload.party_name ?? "").trim();
      return name || null;
    }
    case "process-issue": {
      const view = parseProcessIssuePayload(payload);
      const parts = [view.issueLabel, view.productionOrder].filter(Boolean);
      return parts.length ? parts.join(" · ") : view.note;
    }
    default: {
      const title = String(payload.title ?? "").trim();
      if (title) return title;
      const description = String(payload.description ?? "").trim();
      return description || null;
    }
  }
}

export function requestListRequesterName(row: RequestSummary): string {
  return row.created_by_name?.trim() || "—";
}

/* PRC-REF-023-UX-PARITY-FIX-01 — view model neutro da listagem
 * unificada (requests-api + casos PRC da Engineering API).
 * Apresentação apenas — não é domínio, storage nem fonte de verdade. */

export type UnifiedRequestSource = "requests-api" | "engineering-prc";

export type UnifiedRequestRow = {
  id: string;
  source: UnifiedRequestSource;
  /** Número oficial (requests-api) ou apresentação legível do UUID PRC. */
  displayNumber: string;
  /** Identificador completo e inequívoco (UUID oficial no PRC). */
  fullIdentifier: string;
  typeLabel: string;
  subject: string;
  status: string;
  statusLabel: string;
  statusVariant: "neutral" | "info" | "success" | "warning" | "danger";
  branch: string;
  createdAt: string;
  /** Destino de detalhe correto para a origem da linha. */
  destination: string;
};

export function toUnifiedRow(
  row: RequestSummary,
  typeLabel: string,
  statusLabel: string,
  subject: string,
): UnifiedRequestRow {
  return {
    id: row.id,
    source: "requests-api",
    displayNumber: row.request_number || `#${row.id.slice(0, 8)}`,
    fullIdentifier: row.id,
    typeLabel,
    subject: subject || "—",
    status: row.status,
    statusLabel,
    statusVariant: "info",
    branch: row.branch_code || "—",
    createdAt: row.created_at || "",
    destination: "",
  };
}

const PRC_STATUS_VARIANTS: Record<
  string,
  UnifiedRequestRow["statusVariant"]
> = {
  submitted: "info",
  in_progress: "info",
  needs_information: "warning",
  needs_correction: "warning",
  under_review: "info",
  completed: "success",
  rejected: "danger",
};

/* FIX-02A — semântica da listagem: a coluna Tipo mostra a categoria
 * da solicitação (distinta de Assunto). PRC CREATE → "Criação de
 * matéria-prima"; UPDATE → "Alteração de produto". Assunto = ação:
 * "Criação" ou "Alteração — {código oficial}" (zeros preservados). */
const PRC_LIST_TYPE_LABELS: Record<string, string> = {
  create: "Criação de matéria-prima",
  update: "Alteração de produto",
};

export function prcToUnifiedRow(
  row: {
    id: string;
    requestType: string;
    status: string;
    officialCode?: string | null;
    createdAt: string;
  },
  typeLabels: Record<string, string>,
  statusLabels: Record<string, string>,
  destination: string,
): UnifiedRequestRow {
  const typeLabel =
    PRC_LIST_TYPE_LABELS[row.requestType] ||
    typeLabels[row.requestType] ||
    row.requestType;
  const subject =
    row.requestType === "update"
      ? `Alteração${row.officialCode ? ` — ${row.officialCode}` : ""}`
      : "Criação";
  return {
    id: row.id,
    source: "engineering-prc",
    displayNumber: `PRC-${row.id.slice(0, 8).toUpperCase()}`,
    fullIdentifier: row.id,
    typeLabel,
    subject,
    status: row.status,
    statusLabel: statusLabels[row.status] || row.status,
    statusVariant: PRC_STATUS_VARIANTS[row.status] || "info",
    branch: "—",
    createdAt: row.createdAt || "",
    destination,
  };
}

/** Merge por criação desc — janela honesta entre fontes pagináveis. */
export function mergeUnifiedRows(
  a: UnifiedRequestRow[],
  b: UnifiedRequestRow[],
): UnifiedRequestRow[] {
  return [...a, ...b].sort((x, y) =>
    (y.createdAt || "").localeCompare(x.createdAt || ""),
  );
}
