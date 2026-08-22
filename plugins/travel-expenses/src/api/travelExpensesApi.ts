import { httpBlob, httpForm, httpGet, httpJson } from "./httpClient";

export const API_BASE = "/apps/travel-expenses-api";

export type Envelope<T> = { success: boolean; message: string; data: T };

export type UnitAccess = {
  id: "01" | "02";
  label: string;
  view: boolean;
  write: boolean;
  manage: boolean;
};

export type TravelAccess = {
  admin: boolean;
  canView: boolean;
  canWrite: boolean;
  canManage: boolean;
  units: UnitAccess[];
};

export type Category = { id: string; label: string; sortOrder: number; active: boolean };

export type Receipt = {
  id: string;
  expenseId: string;
  storedName: string;
  originalName: string;
  mimeType: string;
  sizeBytes: number;
};

export type Expense = {
  id: string;
  reportId: string;
  expenseDate: string;
  categoryId: string;
  merchant: string;
  amountBrl: number;
  notes: string;
  receipts: Receipt[];
};

export type Completeness = {
  ready: boolean;
  expenseCount: number;
  receiptCount: number;
  missingReceiptCount: number;
  missingAmountCount: number;
  dateOutsidePeriodCount: number;
  issues: { code: string; message: string; expenseId?: string }[];
};

export type ReportListItem = {
  id: string;
  number: string;
  unitCode: string;
  destination: string;
  status: string;
  totalAmountBrl: number;
  periodStart?: string | null;
  periodEnd?: string | null;
  expenseCount?: number;
  missingReceiptCount?: number;
  createdByName?: string | null;
  updatedAt?: string;
};

export type ReportDetail = ReportListItem & {
  purpose: string;
  costCenterCode?: string | null;
  costCenterLabel?: string | null;
  ownerUserId: string;
  expenses: Expense[];
  completeness: Completeness;
  pixKeyType?: string | null;
  pixKeyValue?: string | null;
};

export type AuditEvent = {
  id: string;
  eventType: string;
  actorName?: string | null;
  createdAt: string;
  payload?: Record<string, unknown>;
};

export async function getAccess() {
  const body = await httpGet<Envelope<TravelAccess>>(`${API_BASE}/access`);
  return body.data;
}

export async function listCategories() {
  const body = await httpGet<Envelope<Category[]>>(`${API_BASE}/categories`);
  return body.data;
}

export async function listReports(params: {
  scope?: "mine" | "unit";
  unit?: string;
  q?: string;
  periodFrom?: string;
  periodTo?: string;
}) {
  const query = new URLSearchParams();
  if (params.scope) query.set("scope", params.scope);
  if (params.unit) query.set("unit", params.unit);
  if (params.q) query.set("q", params.q);
  if (params.periodFrom) query.set("periodFrom", params.periodFrom);
  if (params.periodTo) query.set("periodTo", params.periodTo);
  const suffix = query.toString() ? `?${query}` : "";
  const body = await httpGet<Envelope<ReportListItem[]>>(`${API_BASE}/reports${suffix}`);
  return body.data;
}

export async function createReport(payload: Record<string, unknown>) {
  const body = await httpJson<Envelope<ReportDetail>>("POST", `${API_BASE}/reports`, payload);
  return body.data;
}

export async function getReport(id: string) {
  const body = await httpGet<Envelope<ReportDetail>>(`${API_BASE}/reports/${id}`);
  return body.data;
}

export async function updateReport(id: string, payload: Record<string, unknown>) {
  const body = await httpJson<Envelope<ReportDetail>>("PATCH", `${API_BASE}/reports/${id}`, payload);
  return body.data;
}

export async function deleteReport(id: string) {
  await httpJson("DELETE", `${API_BASE}/reports/${id}`);
}

export async function addExpense(reportId: string, payload: Record<string, unknown>) {
  const body = await httpJson<Envelope<Expense>>(
    "POST",
    `${API_BASE}/reports/${reportId}/expenses`,
    payload,
  );
  return body.data;
}

export async function updateExpense(
  reportId: string,
  expenseId: string,
  payload: Record<string, unknown>,
) {
  const body = await httpJson<Envelope<Expense>>(
    "PATCH",
    `${API_BASE}/reports/${reportId}/expenses/${expenseId}`,
    payload,
  );
  return body.data;
}

export async function deleteExpense(reportId: string, expenseId: string) {
  await httpJson("DELETE", `${API_BASE}/reports/${reportId}/expenses/${expenseId}`);
}

export async function uploadReceipt(reportId: string, expenseId: string, file: File) {
  const form = new FormData();
  form.append("file", file, file.name);
  const body = await httpForm<Envelope<Receipt>>(
    `${API_BASE}/reports/${reportId}/expenses/${expenseId}/receipts`,
    form,
  );
  return body.data;
}

export function receiptFileUrl(reportId: string, expenseId: string, receiptId: string) {
  return `${API_BASE}/reports/${reportId}/expenses/${expenseId}/receipts/${receiptId}/file`;
}

export async function fetchReceiptBlob(reportId: string, expenseId: string, receiptId: string) {
  return httpBlob(receiptFileUrl(reportId, expenseId, receiptId));
}

export async function deleteReceipt(reportId: string, expenseId: string, receiptId: string) {
  await httpJson("DELETE", `${API_BASE}/reports/${reportId}/expenses/${expenseId}/receipts/${receiptId}`);
}

export async function listAudit(reportId: string) {
  const body = await httpGet<Envelope<AuditEvent[]>>(`${API_BASE}/reports/${reportId}/audit`);
  return body.data;
}

export async function downloadPackagePdf(reportId: string) {
  return httpBlob(`${API_BASE}/reports/${reportId}/package.pdf`);
}
