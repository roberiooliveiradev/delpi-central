import { httpGet, suppliesApiUrl } from "../../api/httpClient";
import { CONSUMPTION_AUDIT_CONTENT as C } from "./content";
import type {
  ConsumptionAuditBranch,
  ConsumptionAuditOperation,
  ConsumptionAuditResponse,
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
