import { requestBlob, requestJson } from "./httpClient";
import type { ReportSnapshot, ReportWritePayload } from "../domain/reportForm";

export const API_BASE = "/apps/api-delpi/engineering/metallographic-reports";

export type ImageSlot = "original" | "measured";

export type ReportListItem = ReportSnapshot;

export type ReportList = {
  items: ReportListItem[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
};

export type ReportFilters = {
  page?: number;
  pageSize?: number;
  sort?: "created_at_desc" | "created_at_asc" | "report_date_desc" | "report_number_asc";
  reportDateFrom?: string;
  reportDateTo?: string;
  reportNumber?: string;
  terminalCode?: string;
  terminalPartNumber?: string;
  productHarness?: string;
  cable?: string;
  conductorSection?: string;
  applicatorTool?: string;
  pressEquipment?: string;
  batchProductionOrder?: string;
  sampleIdentification?: string;
  conclusionResult?: "" | "conforming" | "nonconforming";
};

const FILTER_QUERY: Record<keyof ReportFilters, string> = {
  page: "page",
  pageSize: "page_size",
  sort: "sort",
  reportDateFrom: "report_date_from",
  reportDateTo: "report_date_to",
  reportNumber: "report_number",
  terminalCode: "terminal_code",
  terminalPartNumber: "terminal_part_number",
  productHarness: "product_harness",
  cable: "cable",
  conductorSection: "conductor_section",
  applicatorTool: "applicator_tool",
  pressEquipment: "press_equipment",
  batchProductionOrder: "batch_production_order",
  sampleIdentification: "sample_identification",
  conclusionResult: "conclusion_result",
};

export function listQuery(filters: ReportFilters): string {
  const params = new URLSearchParams();
  for (const [key, query] of Object.entries(FILTER_QUERY) as [keyof ReportFilters, string][]) {
    const value = filters[key];
    if (value === undefined || value === null || value === "") continue;
    params.set(query, String(value));
  }
  const text = params.toString();
  return text ? `?${text}` : "";
}

export function listReports(filters: ReportFilters, signal?: AbortSignal) {
  return requestJson<ReportList>(`${API_BASE}${listQuery(filters)}`, { signal });
}

export function getReport(reportId: string, signal?: AbortSignal) {
  return requestJson<ReportSnapshot>(`${API_BASE}/${reportId}`, { signal });
}

export function createReport(payload: ReportWritePayload, idempotencyKey: string) {
  return requestJson<ReportSnapshot>(API_BASE, {
    method: "POST",
    body: JSON.stringify(payload),
    idempotencyKey,
  });
}

export function updateReport(reportId: string, payload: ReportWritePayload, ifMatch: string) {
  return requestJson<ReportSnapshot>(`${API_BASE}/${reportId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    ifMatch,
  });
}

export function deleteReport(reportId: string, ifMatch: string) {
  return requestJson<{ id: string; deleted: boolean; version: number }>(`${API_BASE}/${reportId}`, {
    method: "DELETE",
    ifMatch,
  });
}

export function copyReport(reportId: string, idempotencyKey: string) {
  return requestJson<ReportSnapshot>(`${API_BASE}/${reportId}/copies`, {
    method: "POST",
    idempotencyKey,
  });
}

export function putImage(reportId: string, slot: ImageSlot, file: Blob, contentType: string, ifMatch: string) {
  const body = new FormData();
  const extension = contentType.includes("png") ? "png" : "jpg";
  body.append("file", file, `${slot}.${extension}`);
  return requestJson<{ slot: string; version: number }>(`${API_BASE}/${reportId}/images/${slot}`, {
    method: "PUT",
    body,
    ifMatch,
  });
}

export function deleteImage(reportId: string, slot: ImageSlot, ifMatch: string) {
  return requestJson<{ slot: string; deleted: boolean; version: number }>(
    `${API_BASE}/${reportId}/images/${slot}`,
    { method: "DELETE", ifMatch },
  );
}

export function getImage(reportId: string, slot: ImageSlot) {
  return requestBlob(`${API_BASE}/${reportId}/images/${slot}`);
}

export function exportPdf(reportId: string) {
  return requestBlob(`${API_BASE}/${reportId}/pdf`);
}
