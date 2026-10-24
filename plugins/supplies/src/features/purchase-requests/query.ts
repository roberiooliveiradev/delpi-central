import { resolvePeriodPreset } from "../../app/periodPreset";
import {
  canonicalizeUiBranches,
  normalizeSuppliesUnitCode,
  resolveRequestedBranches,
} from "../../app/suppliesUnits";
import type {
  OverallStage,
  PurchaseRequestDetailLine,
  PurchaseRequestLinkedOrder,
  PurchaseRequestReceipt,
  PurchaseRequestTimelineEvent,
  PurchaseRequestsQuery,
  PurchaseRequestsSortDir,
} from "./types";
import { DEFAULT_PAGE_SIZE, OVERALL_STAGE_VALUES } from "./types";

export const PURCHASE_REQUESTS_SORTABLE_COLUMNS = {
  request_number: "request_number",
  request_item: "request_item",
  product: "product_code",
  requester: "requester",
  cost_center: "cost_center",
  opened: "issue_date",
  stage: "overall_stage",
} as const;

export type PurchaseRequestSortableColumnKey = keyof typeof PURCHASE_REQUESTS_SORTABLE_COLUMNS;

/** Same default chip as Overview («Este mês»). */
export function defaultPeriod(): { date_from: string; date_to: string } {
  const range = resolvePeriodPreset("this_month");
  if (!range) {
    throw new Error("resolvePeriodPreset(this_month) must resolve");
  }
  return { date_from: range.from, date_to: range.to };
}

/** UI default: empty branches = «Todas» (API expands via authorizeQueryBranches). */
export function createDefaultQuery(): PurchaseRequestsQuery {
  const period = defaultPeriod();
  return {
    branches: [],
    date_from: period.date_from,
    date_to: period.date_to,
    request_number: "",
    product_code: "",
    requester_ids: [],
    cost_centers: [],
    overall_stages: [],
    sort_by: "",
    sort_dir: "desc",
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    request: "",
  };
}

export function buildListSearchParams(
  query: PurchaseRequestsQuery,
  options?: { includePagination?: boolean; includeStages?: boolean },
): URLSearchParams {
  const params = new URLSearchParams();
  for (const branch of query.branches) {
    const code = normalizeSuppliesUnitCode(branch);
    if (code) params.append("branch", code);
  }
  if (query.date_from.trim()) params.set("date_from", query.date_from.trim());
  if (query.date_to.trim()) params.set("date_to", query.date_to.trim());
  if (query.request_number.trim()) params.set("request_number", query.request_number.trim());
  if (query.product_code.trim()) params.set("product_code", query.product_code.trim());
  for (const pid of query.requester_ids) {
    const id = pid.trim();
    if (id) params.append("requester_user_id", id);
  }
  for (const cc of query.cost_centers) {
    const code = cc.trim();
    if (code) params.append("cost_center", code);
  }
  if (options?.includeStages !== false) {
    for (const stage of query.overall_stages) {
      params.append("overall_stage", stage);
    }
  }
  if (query.sort_by.trim()) {
    params.set("sort_by", query.sort_by.trim());
    params.set("sort_dir", query.sort_dir === "asc" ? "asc" : "desc");
  }
  if (options?.includePagination !== false) {
    params.set("page", String(query.page));
    params.set("page_size", String(query.page_size));
  }
  return params;
}

export function buildRequestKey(branch: string, requestNumber: string): string {
  return `${branch}:${requestNumber}`;
}

export function parseRequestKey(raw: string): { branch: string; requestNumber: string } | null {
  const trimmed = raw.trim();
  if (!trimmed.includes(":")) return null;
  const [branch, ...rest] = trimmed.split(":");
  const requestNumber = rest.join(":").trim();
  if (!branch?.trim() || !requestNumber) return null;
  return { branch: branch.trim(), requestNumber };
}

function readParam(params: URLSearchParams, key: string): string {
  return (params.get(key) ?? "").trim();
}

function readInt(params: URLSearchParams, key: string, fallback: number): number {
  const parsed = Number.parseInt(readParam(params, key), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function readSortDir(raw: string): PurchaseRequestsSortDir {
  return raw.toLowerCase() === "asc" ? "asc" : "desc";
}

export function parseQueryFromSearch(
  search: string,
  allowedUnits: readonly string[] = [],
): PurchaseRequestsQuery {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const defaults = createDefaultQuery();
  const allowed = new Set<string>(OVERALL_STAGE_VALUES);
  const stages = params
    .getAll("overall_stage")
    .map((item) => item.trim())
    .filter((item): item is OverallStage => allowed.has(item));
  const fromUrl = params
    .getAll("branch")
    .map((value) => normalizeSuppliesUnitCode(value))
    .filter(Boolean);
  return {
    branches:
      fromUrl.length === 0
        ? []
        : allowedUnits.length
          ? canonicalizeUiBranches(fromUrl, allowedUnits)
          : [...new Set(fromUrl)],
    date_from: readParam(params, "date_from") || defaults.date_from,
    date_to: readParam(params, "date_to") || defaults.date_to,
    request_number: readParam(params, "request_number"),
    product_code: readParam(params, "product_code"),
    requester_ids: [
      ...new Set(
        params
          .getAll("requester_user_id")
          .map((item) => item.trim())
          .filter(Boolean),
      ),
    ],
    cost_centers: [
      ...new Set(
        params
          .getAll("cost_center")
          .map((item) => item.trim())
          .filter(Boolean),
      ),
    ],
    overall_stages: stages,
    sort_by: readParam(params, "sort_by"),
    sort_dir: readSortDir(readParam(params, "sort_dir")),
    page: readInt(params, "page", 1),
    page_size: readInt(params, "page_size", DEFAULT_PAGE_SIZE),
    request: readParam(params, "request"),
  };
}

export function nextServerSort(
  current: PurchaseRequestsQuery,
  columnKey: string,
): Pick<PurchaseRequestsQuery, "sort_by" | "sort_dir" | "page"> | null {
  const sortBy =
    PURCHASE_REQUESTS_SORTABLE_COLUMNS[columnKey as PurchaseRequestSortableColumnKey];
  if (!sortBy) return null;
  if (current.sort_by === sortBy) {
    return {
      sort_by: sortBy,
      sort_dir: current.sort_dir === "asc" ? "desc" : "asc",
      page: 1,
    };
  }
  return { sort_by: sortBy, sort_dir: "asc", page: 1 };
}

export function tableSortKey(sortBy: string): string | null {
  const entry = Object.entries(PURCHASE_REQUESTS_SORTABLE_COLUMNS).find(
    ([, field]) => field === sortBy,
  );
  return entry?.[0] ?? null;
}

export function authorizeQueryBranches(
  query: PurchaseRequestsQuery,
  allowedUnits: readonly string[],
): PurchaseRequestsQuery {
  return {
    ...query,
    branches: resolveRequestedBranches(query.branches, allowedUnits),
  };
}

export function buildUrlSearch(query: PurchaseRequestsQuery): string {
  const params = buildListSearchParams(query);
  if (query.request.trim()) params.set("request", query.request.trim());
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function formatDatePtBr(iso: string | null | undefined): string {
  if (!iso) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function labelOverallStage(stage: string | null | undefined): string {
  switch (stage) {
    case "awaiting_order":
      return "Aguardando pedido";
    case "partially_ordered":
      return "Pedido parcial";
    case "ordered":
      return "Pedido emitido";
    case "awaiting_receipt":
      return "Aguardando entrega";
    case "partially_received":
      return "Recebimento parcial";
    case "completed":
      return "Concluída";
    case "residual_closed":
      return "Encerrada por resíduo";
    default:
      return stage || "—";
  }
}

export function formatRequestNumber(value: string | null | undefined): string {
  const trimmed = (value || "").trim();
  return trimmed || "—";
}

export function formatProductLabel(
  code: string | null | undefined,
  description: string | null | undefined,
): string {
  const c = (code || "").trim();
  const d = (description || "").trim();
  if (c && d) return `${c} — ${d}`;
  return c || d || "—";
}

/** Badge tone for the canonical SC stages — single source for list, cards and detail. */
export function stageBadgeVariant(
  stage: string | null | undefined,
): "neutral" | "info" | "success" | "warning" | "danger" {
  switch (stage) {
    case "awaiting_order":
    case "awaiting_receipt":
      return "warning";
    case "partially_ordered":
    case "ordered":
    case "partially_received":
      return "info";
    case "completed":
      return "success";
    case "residual_closed":
      return "neutral";
    default:
      return "neutral";
  }
}

export function isKnownOverallStage(
  stage: string | null | undefined,
): stage is OverallStage {
  return Boolean(
    stage && (OVERALL_STAGE_VALUES as readonly string[]).includes(stage),
  );
}

/** Canonical approval label for detail header (C1_APROV mapped by producer). */
export function labelApprovalStatus(
  status: string | null | undefined,
  labels: {
    approved: string;
    rejected: string;
    blocked: string;
    unknown: string;
  },
): string {
  switch ((status || "").trim()) {
    case "approved":
      return labels.approved;
    case "rejected":
      return labels.rejected;
    case "blocked":
      return labels.blocked;
    default:
      return labels.unknown;
  }
}

export function approvalBadgeVariant(
  status: string | null | undefined,
): "neutral" | "success" | "warning" | "danger" {
  switch ((status || "").trim()) {
    case "approved":
      return "success";
    case "rejected":
      return "danger";
    case "blocked":
      return "warning";
    default:
      return "neutral";
  }
}

/**
 * Distinct linked purchase orders by canonical identity (branch, order_number).
 * Entries with an incomplete identity (blank branch or number) are never
 * counted — a missing key must not collapse into a fake "1 order" bucket.
 */
export function countLinkedOrders(
  orders:
    | ReadonlyArray<{
        branch?: string | null;
        order_number?: string | null;
      }>
    | null
    | undefined,
): number {
  if (!orders?.length) return 0;
  const keys = new Set<string>();
  for (const order of orders) {
    const branch = (order.branch ?? "").trim();
    const number = (order.order_number ?? "").trim();
    if (!branch || !number) continue;
    keys.add(`${branch}|${number}`);
  }
  return keys.size;
}

/** True when the order carries a complete (branch, order_number) identity — linkable. */
export function hasCompleteOrderIdentity(
  order: { branch?: string | null; order_number?: string | null } | null | undefined,
): boolean {
  return Boolean(order?.branch?.trim() && order?.order_number?.trim());
}

/**
 * Distinct approver names across visible lines — approval is per-line
 * (C1_NOMAPRO); never promote a single line approver to the header.
 * Returns the deduped, trimmed names in payload order.
 */
export function uniqueApproverNames(
  lines:
    | ReadonlyArray<{
        approval?: { approver_name?: string | null } | null;
      }>
    | null
    | undefined,
): string[] {
  const seen = new Set<string>();
  const names: string[] = [];
  for (const line of lines ?? []) {
    const name = (line.approval?.approver_name || "").trim();
    if (name && !seen.has(name)) {
      seen.add(name);
      names.push(name);
    }
  }
  return names;
}

export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
}

export function formatMoneyBr(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  });
}

/** Quantity always displayed with its own unit — never a unitless sum. */
export function formatQuantityWithUnit(
  value: number | null | undefined,
  unit: string | null | undefined,
): string {
  const qty = formatQuantity(value);
  const um = (unit || "").trim();
  if (qty === "—") return "—";
  return um ? `${qty} ${um}` : qty;
}

/**
 * Deduped enriched order lines across the visible request lines
 * (identity = branch + order_number + order_item). Full quantities,
 * dates and receipts live only at line level — the header carries a
 * supplier/order summary.
 */
export function collectLinkedOrders(
  lines: ReadonlyArray<Pick<PurchaseRequestDetailLine, "purchase_orders">> | null | undefined,
): PurchaseRequestLinkedOrder[] {
  const seen = new Set<string>();
  const orders: PurchaseRequestLinkedOrder[] = [];
  for (const line of lines ?? []) {
    for (const order of line.purchase_orders ?? []) {
      const key = `${order.branch ?? ""}|${order.order_number ?? ""}|${order.order_item ?? ""}`;
      if (seen.has(key)) continue;
      seen.add(key);
      orders.push(order);
    }
  }
  return orders;
}

/** Flattened receipts with their linked-order context preserved. */
export function collectReceipts(
  orders: ReadonlyArray<PurchaseRequestLinkedOrder> | null | undefined,
): PurchaseRequestReceipt[] {
  const receipts: PurchaseRequestReceipt[] = [];
  for (const order of orders ?? []) {
    for (const receipt of order.receipts ?? []) {
      receipts.push(receipt);
    }
  }
  return receipts;
}

/** Producer vocabulary for linked-order delivery (SC context, not PC list). */
export function labelLinkedOrderDeliveryStatus(
  status: string | null | undefined,
): string {
  switch ((status || "").trim()) {
    case "received":
      return "Recebido";
    case "overdue":
      return "Em atraso";
    case "on_time":
      return "No prazo";
    case "not_applicable":
      return "Não aplicável";
    default:
      return status || "—";
  }
}

export function linkedOrderDeliveryVariant(
  status: string | null | undefined,
): "neutral" | "info" | "success" | "danger" {
  switch ((status || "").trim()) {
    case "received":
      return "success";
    case "overdue":
      return "danger";
    case "on_time":
      return "info";
    default:
      return "neutral";
  }
}

/**
 * Timeline tone: `expected_delivery` is a planned milestone (marked in copy
 * as well), every other emitted type is an occurred event.
 */
export function timelineEventTone(
  type: string | null | undefined,
): "neutral" | "info" | "warning" | "danger" {
  return type === "expected_delivery" ? "info" : "neutral";
}

/** Short context for a derived timeline event (PC, NF or SC item reference). */
export function timelineReferenceLabel(
  event: PurchaseRequestTimelineEvent,
  formatters: {
    order: (number: string) => string;
    invoice: (number: string) => string;
    item: (item: string) => string;
  },
): string {
  const ref = event.reference ?? {};
  const parts: string[] = [];
  const orderNumber = (ref.order_number ?? "").trim();
  const invoiceNumber = (ref.invoice_number ?? "").trim();
  const requestItem = (ref.request_item ?? "").trim();
  if (orderNumber) parts.push(formatters.order(orderNumber));
  if (invoiceNumber) parts.push(formatters.invoice(invoiceNumber));
  if (requestItem) parts.push(formatters.item(requestItem));
  return parts.join(" · ");
}
