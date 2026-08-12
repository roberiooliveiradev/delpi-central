import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  Shipment,
  ShipmentsPage,
  SummaryData,
  ThirdPartyMaterialsQuery,
} from "../types/thirdPartyMaterials";
import { queryString } from "../utils/queryParams";
import { httpGet, httpGetBlob, type HttpRequestOptions } from "./httpClient";

const API_BASE = "/apps/api-delpi/supplies/third-party-materials";

function sharedQuery(query: ThirdPartyMaterialsQuery) {
  return {
    branch: query.branch,
    product: query.product || undefined,
    customer_reference: query.customerReference || undefined,
    partner_code: query.partnerCode || undefined,
    partner_store: query.partnerStore || undefined,
    receipt_number: query.receiptNumber || undefined,
    return_number: query.returnNumber || undefined,
    issued_from: query.issuedFrom || undefined,
    issued_to: query.issuedTo || undefined,
    status: query.status || undefined,
    only_with_balance: query.onlyWithBalance || undefined,
    include_test_products: query.includeTestProducts || undefined,
  };
}

async function getEnvelope<T>(path: string, options: HttpRequestOptions = {}): Promise<T> {
  const payload = await httpGet<unknown>(`${API_BASE}${path}`, options);
  return unwrapApiDelpiEnvelope<T>(payload);
}

export async function fetchSummary(
  query: ThirdPartyMaterialsQuery,
  options: HttpRequestOptions = {},
): Promise<SummaryData> {
  return getEnvelope<SummaryData>(`/summary${queryString(sharedQuery(query))}`, options);
}

export async function fetchShipments(
  query: ThirdPartyMaterialsQuery,
  page: number,
  pageSize: number,
  options: HttpRequestOptions = {},
): Promise<ShipmentsPage> {
  return getEnvelope<ShipmentsPage>(
    `/shipments${queryString({ ...sharedQuery(query), page, page_size: pageSize })}`,
    options,
  );
}

export async function fetchShipment(
  shipmentRecno: number,
  branch: string,
  includeTestProducts: boolean,
  options: HttpRequestOptions = {},
): Promise<Shipment> {
  return getEnvelope<Shipment>(
    `/shipments/${shipmentRecno}${queryString({
      branch,
      include_test_products: includeTestProducts || undefined,
    })}`,
    options,
  );
}

export async function exportReturns(
  query: ThirdPartyMaterialsQuery,
  exportFormat: "csv" | "xlsx",
  options: HttpRequestOptions = {},
): Promise<{ blob: Blob; filename: string }> {
  const result = await httpGetBlob(
    `${API_BASE}/returns/export${queryString({
      ...sharedQuery(query),
      export_format: exportFormat,
    })}`,
    options,
  );
  return { blob: result.blob, filename: result.filename };
}
