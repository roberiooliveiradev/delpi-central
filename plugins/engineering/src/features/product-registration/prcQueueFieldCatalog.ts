/** Catálogo único de campos da fila PRC — mesma fonte para Tabela,
 * Cards e Kanban. Preferências (`engineering:prc:requests:columns`)
 * controlam visibilidade e ordem nos três modos. */

import type { ReactNode } from "react";

import type { PrcRequestSummary } from "./api/productRegistrationApi";
import {
  PRC_COPY,
  PRC_STATUS_LABELS,
  PRC_TYPE_LABELS,
  prcShortId,
} from "./prcCopy";

export const PRC_QUEUE_FIELD_KEYS = [
  "id",
  "type",
  "requester",
  "officialCode",
  "createdAt",
  "status",
  "assignedTo",
] as const;

export type PrcQueueFieldKey = (typeof PRC_QUEUE_FIELD_KEYS)[number];

export const PRC_QUEUE_FIELD_LABELS: Record<PrcQueueFieldKey, string> = {
  id: "Nº",
  type: "Tipo",
  requester: "Solicitante",
  officialCode: "Código oficial",
  createdAt: "Abertura",
  status: "Status",
  assignedTo: "Responsável",
};

/** Slot visual do card — hierarquia estável; a ordem do usuário
 * prevalece dentro de cada slot. */
export type PrcQueueCardSlot = "header" | "highlight" | "detail";

export const PRC_QUEUE_FIELD_SLOTS: Record<PrcQueueFieldKey, PrcQueueCardSlot> = {
  id: "header",
  status: "header",
  officialCode: "highlight",
  type: "highlight",
  createdAt: "detail",
  requester: "detail",
  assignedTo: "detail",
};

export const PRC_QUEUE_COLUMN_CATALOG = PRC_QUEUE_FIELD_KEYS.map((key) => ({
  key,
  label: PRC_QUEUE_FIELD_LABELS[key],
}));

export function isPrcQueueFieldKey(value: string): value is PrcQueueFieldKey {
  return (PRC_QUEUE_FIELD_KEYS as readonly string[]).includes(value);
}

/** Ordem efetiva: preferência do usuário ∩ catálogo; fallback = padrão. */
export function resolvePrcQueueFieldOrder(
  preferredOrder?: readonly string[] | null,
): PrcQueueFieldKey[] {
  if (!preferredOrder || preferredOrder.length === 0) {
    return [...PRC_QUEUE_FIELD_KEYS];
  }
  const seen = new Set<PrcQueueFieldKey>();
  const ordered: PrcQueueFieldKey[] = [];
  for (const key of preferredOrder) {
    if (isPrcQueueFieldKey(key) && !seen.has(key)) {
      ordered.push(key);
      seen.add(key);
    }
  }
  for (const key of PRC_QUEUE_FIELD_KEYS) {
    if (!seen.has(key)) ordered.push(key);
  }
  return ordered;
}

export function resolveVisiblePrcQueueFields(options: {
  visibility: Record<string, boolean | undefined>;
  order?: readonly string[] | null;
  /** Quando true (Kanban), omite Status no card — a coluna já agrupa. */
  omitStatus?: boolean;
  /** Identidade sempre acessível no card mesmo se Nº estiver oculto. */
  forceIdentity?: boolean;
}): PrcQueueFieldKey[] {
  const order = resolvePrcQueueFieldOrder(options.order);
  const visible = order.filter((key) => {
    if (options.omitStatus && key === "status") return false;
    if (options.visibility[key] === false) return false;
    return true;
  });
  if (options.forceIdentity && !visible.includes("id")) {
    return ["id", ...visible];
  }
  return visible;
}

export function formatPrcQueueCreatedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("pt-BR");
}

export function prcQueueOfficialCodeText(
  row: Pick<PrcRequestSummary, "officialCode">,
): string {
  const code = (row.officialCode || "").trim();
  return code || PRC_COPY.awaitingCode;
}

export function prcQueueTypeText(
  row: Pick<PrcRequestSummary, "requestType">,
): string {
  return PRC_TYPE_LABELS[row.requestType] || row.requestType;
}

export function prcQueueStatusText(
  row: Pick<PrcRequestSummary, "status">,
): string {
  return PRC_STATUS_LABELS[row.status] || row.status;
}

export function prcQueueRequesterText(
  row: Pick<PrcRequestSummary, "requester">,
): string {
  return (row.requester.displayName || "").trim() || row.requester.subject;
}

export function prcQueueAssigneeText(
  row: Pick<PrcRequestSummary, "assignedTo" | "assignedToDisplayName">,
): string {
  if (!row.assignedTo) return PRC_COPY.unassigned;
  return (row.assignedToDisplayName || "").trim() || row.assignedTo;
}

/** Valor textual canônico — paridade informacional Tabela/Cards/Kanban. */
export function getPrcQueueFieldPlainText(
  row: PrcRequestSummary,
  key: PrcQueueFieldKey,
): string {
  switch (key) {
    case "id":
      return prcShortId(row.id);
    case "type":
      return prcQueueTypeText(row);
    case "requester":
      return prcQueueRequesterText(row);
    case "officialCode":
      return prcQueueOfficialCodeText(row);
    case "createdAt":
      return formatPrcQueueCreatedAt(row.createdAt);
    case "status":
      return prcQueueStatusText(row);
    case "assignedTo":
      return prcQueueAssigneeText(row);
    default: {
      const _exhaustive: never = key;
      return _exhaustive;
    }
  }
}

export type PrcQueueCardFieldTone = "title" | "value" | "meta";

export function prcQueueCardFieldTone(
  key: PrcQueueFieldKey,
): PrcQueueCardFieldTone {
  if (key === "id" || key === "officialCode") return "title";
  if (key === "status" || key === "type") return "value";
  return "meta";
}

/** Agrupa campos visíveis por slot preservando a ordem preferida. */
export function groupPrcQueueFieldsBySlot(
  keys: readonly PrcQueueFieldKey[],
): Record<PrcQueueCardSlot, PrcQueueFieldKey[]> {
  const groups: Record<PrcQueueCardSlot, PrcQueueFieldKey[]> = {
    header: [],
    highlight: [],
    detail: [],
  };
  for (const key of keys) {
    groups[PRC_QUEUE_FIELD_SLOTS[key]].push(key);
  }
  return groups;
}

export type PrcKanbanColumnCount = {
  status: string;
  totalInScope: number;
  displayedOnPage: number;
};

/** Contagem honesta: total do escopo filtrado ≠ itens da página. */
export function formatPrcKanbanColumnCountMeta(
  counts: PrcKanbanColumnCount,
): string {
  const total = Math.max(0, counts.totalInScope);
  const displayed = Math.max(0, counts.displayedOnPage);
  if (total === 0 && displayed === 0) {
    return "0 no total · 0 nesta página";
  }
  return `${total} no total · ${displayed} nesta página`;
}

export type PrcQueueFieldRenderers = {
  id: (row: PrcRequestSummary) => ReactNode;
  type: (row: PrcRequestSummary) => ReactNode;
  requester: (row: PrcRequestSummary) => ReactNode;
  officialCode: (row: PrcRequestSummary) => ReactNode;
  createdAt: (row: PrcRequestSummary) => ReactNode;
  status: (row: PrcRequestSummary) => ReactNode;
  assignedTo: (row: PrcRequestSummary) => ReactNode;
};
