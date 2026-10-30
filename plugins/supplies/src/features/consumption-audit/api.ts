import { httpGet, suppliesApiUrl } from "../../api/httpClient";
import { CONSUMPTION_AUDIT_CONTENT as C } from "./content";
import type {
  ConsumptionAuditBranch,
  ConsumptionAuditComparisonResponse,
  ConsumptionAuditDateType,
  ConsumptionAuditOperation,
  ConsumptionAuditOrderSummary,
  ConsumptionAuditResponse,
  ConsumptionAuditSearchPage,
} from "./types";

/** Chave canônica da OP — C2_NUM(6) + C2_ITEM(2) + C2_SEQUEN(3). */
export const PRODUCTION_ORDER_RE = /^[0-9A-Z]{11}$/;

/**
 * 200 com payload fora do contrato NÃO é empty-state: o guard transforma
 * shape inválido em erro de integração explícito (mesmo critério de E11).
 */
export class ConsumptionAuditContractError extends Error {
  constructor() {
    super(C.invalidResponse);
    this.name = "ConsumptionAuditContractError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isOperation(value: unknown): value is ConsumptionAuditOperation {
  if (!isRecord(value)) return false;
  return (
    typeof value.operation === "string" &&
    typeof value.work_center === "string" &&
    Array.isArray(value.components) &&
    isRecord(value.execution_evidence)
  );
}

export function isConsumptionAuditResponse(
  value: unknown,
): value is ConsumptionAuditResponse {
  if (!isRecord(value)) return false;
  return (
    typeof value.production_order === "string" &&
    typeof value.branch === "string" &&
    isRecord(value.order) &&
    typeof value.order.product_code === "string" &&
    Array.isArray(value.operations) &&
    value.operations.every(isOperation) &&
    Array.isArray(value.unmatched_movements) &&
    Array.isArray(value.related_orders) &&
    isRecord(value.quality) &&
    isStringArray(value.quality.warnings) &&
    isRecord(value.metadata)
  );
}

export type ConsumptionAuditQuery = {
  unit: ConsumptionAuditBranch;
  productionOrder: string;
};

export async function getConsumptionAuditOrder(
  query: ConsumptionAuditQuery,
  signal?: AbortSignal,
): Promise<ConsumptionAuditResponse> {
  const op = query.productionOrder.trim().toUpperCase();
  const params = new URLSearchParams({ unit: query.unit });
  const payload = await httpGet<unknown>(
    suppliesApiUrl(
      `/consumption-audit/orders/${encodeURIComponent(op)}?${params.toString()}`,
    ),
    { signal },
  );
  if (!isConsumptionAuditResponse(payload)) {
    throw new ConsumptionAuditContractError();
  }
  return payload;
}

// ——— F1 · busca/listagem ———

function isOrderSummary(value: unknown): value is ConsumptionAuditOrderSummary {
  if (!isRecord(value)) return false;
  return (
    typeof value.production_order === "string" &&
    typeof value.order_number === "string" &&
    typeof value.product_code === "string" &&
    typeof value.status === "string"
  );
}

export function isConsumptionAuditSearchPage(
  value: unknown,
): value is ConsumptionAuditSearchPage {
  if (!isRecord(value)) return false;
  return (
    Array.isArray(value.items) &&
    value.items.every(isOrderSummary) &&
    typeof value.page === "number" &&
    typeof value.page_size === "number" &&
    typeof value.total === "number" &&
    typeof value.total_pages === "number"
  );
}

export type ConsumptionAuditSearchFilters = {
  unit: ConsumptionAuditBranch;
  search?: string;
  product?: string;
  dateType?: ConsumptionAuditDateType;
  periodStart?: string;
  periodEnd?: string;
  status?: string;
  workCenter?: string;
  operation?: string;
  page?: number;
  pageSize?: number;
};

const SEARCH_DATE_TYPES = new Set(["emission", "finished", "appointment"]);

export async function searchConsumptionAuditOrders(
  filters: ConsumptionAuditSearchFilters,
  signal?: AbortSignal,
): Promise<ConsumptionAuditSearchPage> {
  const params = new URLSearchParams({ unit: filters.unit });
  const search = (filters.search ?? "").trim().toUpperCase();
  if (search) params.set("search", search);
  const product = (filters.product ?? "").trim();
  if (product) params.set("product", product);
  const dateType = filters.dateType ?? "emission";
  if (SEARCH_DATE_TYPES.has(dateType)) params.set("date_type", dateType);
  if (filters.periodStart) params.set("period_start", filters.periodStart);
  if (filters.periodEnd) params.set("period_end", filters.periodEnd);
  const status = (filters.status ?? "").trim();
  if (status) params.set("status", status);
  const workCenter = (filters.workCenter ?? "").trim();
  if (workCenter) params.set("work_center", workCenter);
  const operation = (filters.operation ?? "").trim();
  if (operation) params.set("operation", operation);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? 25));

  const payload = await httpGet<unknown>(
    suppliesApiUrl(`/consumption-audit/orders?${params.toString()}`),
    { signal },
  );
  if (!isConsumptionAuditSearchPage(payload)) {
    throw new ConsumptionAuditContractError();
  }
  return payload;
}

// ——— F4 · comparação ———

export function isConsumptionAuditComparison(
  value: unknown,
): value is ConsumptionAuditComparisonResponse {
  if (!isRecord(value)) return false;
  return (
    typeof value.branch === "string" &&
    Array.isArray(value.items) &&
    value.items.every(
      (item) =>
        isRecord(item) &&
        typeof item.production_order === "string" &&
        Array.isArray(item.operations) &&
        Array.isArray(item.totals_by_unit),
    ) &&
    Array.isArray(value.not_found)
  );
}

export async function getConsumptionAuditComparison(
  unit: ConsumptionAuditBranch,
  orders: string[],
  signal?: AbortSignal,
): Promise<ConsumptionAuditComparisonResponse> {
  const params = new URLSearchParams({
    unit,
    orders: orders.join(","),
  });
  const payload = await httpGet<unknown>(
    suppliesApiUrl(`/consumption-audit/comparison?${params.toString()}`),
    { signal },
  );
  if (!isConsumptionAuditComparison(payload)) {
    throw new ConsumptionAuditContractError();
  }
  return payload;
}
