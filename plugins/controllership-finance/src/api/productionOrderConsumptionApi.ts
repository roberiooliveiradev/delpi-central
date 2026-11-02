/** Cliente da BFF — visão operacional R04 Consumo por OP.
 *
 * `GET /closing/competences/{period}/production-order-consumption` —
 * reuso governado do produtor consumption-audit da api-delpi
 * (SC2/SG1/SD4/SD3 read-only). Visão operacional; equivalência MATR860
 * não homologada.
 */
import { cfApiUrl, httpGet } from "./httpClient";

export type DateType = "emission" | "finished" | "appointment";

export type ProductionOrderConsumptionParams = {
  period: string;
  branch: "01" | "02";
  search?: string;
  product?: string;
  dateType?: DateType;
  status?: string;
  workCenter?: string;
  operation?: string;
  page?: number;
  pageSize?: number;
};

export type ProductionOrderConsumptionPayload = Record<string, unknown> & {
  items?: unknown[];
  orders?: unknown[];
  page?: number;
  pageSize?: number;
  total?: number;
  period?: string;
  branch?: string;
  dateType?: string;
  officiality?: string;
  officialParity?: string;
  provenance?: string;
  limitations?: string[];
};

type CfEnvelope<T> = {
  success: boolean;
  message?: string;
  data: T;
  meta?: Record<string, unknown>;
};

/**
 * O produtor consumption-audit serializa em snake_case (contrato
 * api-delpi). O adapter publica aliases camelCase para os consumers —
 * sem reescrever nem inventar campos: campos ausentes permanecem
 * ausência tipada.
 */
const SNAKE_TO_CAMEL: Record<string, string> = {
  production_order: "productionOrder",
  order_number: "orderNumber",
  order_item: "orderItem",
  order_sequence: "orderSequence",
  product_code: "productCode",
  product_description: "productDescription",
  unit_of_measure: "unitOfMeasure",
  planned_quantity: "plannedQuantity",
  produced_quantity: "producedQuantity",
  order_type: "orderType",
  emission_date: "emissionDate",
  planned_start_date: "plannedStartDate",
  due_date: "dueDate",
  finished_at: "finishedAt",
  work_center: "workCenter",
  appointment_date: "appointmentDate",
};

function normalizeRow(row: unknown): unknown {
  if (!row || typeof row !== "object" || Array.isArray(row)) return row;
  const out: Record<string, unknown> = {
    ...(row as Record<string, unknown>),
  };
  for (const [snake, camel] of Object.entries(SNAKE_TO_CAMEL)) {
    if (out[camel] === undefined && out[snake] !== undefined) {
      out[camel] = out[snake];
    }
  }
  return out;
}

function normalizePayload(
  payload: ProductionOrderConsumptionPayload,
): ProductionOrderConsumptionPayload {
  const out: ProductionOrderConsumptionPayload = { ...payload };
  for (const key of ["items", "orders"] as const) {
    const list = out[key];
    if (Array.isArray(list)) {
      out[key] = list.map(normalizeRow);
    }
  }
  return out;
}

export function getProductionOrderConsumption(
  params: ProductionOrderConsumptionParams,
): Promise<ProductionOrderConsumptionPayload> {
  const query = new URLSearchParams({
    branch: params.branch,
    date_type: params.dateType ?? "emission",
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 25),
  });
  if (params.search) query.set("search", params.search);
  if (params.product) query.set("product", params.product);
  if (params.status) query.set("status", params.status);
  if (params.workCenter) query.set("work_center", params.workCenter);
  if (params.operation) query.set("operation", params.operation);
  return httpGet<CfEnvelope<ProductionOrderConsumptionPayload>>(
    cfApiUrl(
      `/closing/competences/${encodeURIComponent(
        params.period,
      )}/production-order-consumption?${query.toString()}`,
    ),
  ).then((envelope) => normalizePayload(envelope.data));
}

export function getProductionOrderConsumptionDetail(
  period: string,
  productionOrder: string,
  branch: "01" | "02",
): Promise<ProductionOrderConsumptionPayload> {
  const query = new URLSearchParams({ branch });
  return httpGet<CfEnvelope<ProductionOrderConsumptionPayload>>(
    cfApiUrl(
      `/closing/competences/${encodeURIComponent(
        period,
      )}/production-order-consumption/${encodeURIComponent(
        productionOrder,
      )}?${query.toString()}`,
    ),
  ).then((envelope) => normalizePayload(envelope.data));
}
