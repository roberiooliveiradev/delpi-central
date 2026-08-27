import type { OverallStage, PurchaseRequestsQuery } from "../types/purchaseRequests";
import { OVERALL_STAGE_VALUES } from "../types/purchaseRequests";
import { defaultPeriod } from "./formatters";

export const BASE_PATH = "/apps/purchase-requests";

export type UrlState = PurchaseRequestsQuery & {
  request: string;
};

export function createDefaultUrlState(branch: string): UrlState {
  const period = defaultPeriod();
  return {
    branch,
    date_from: period.date_from,
    date_to: period.date_to,
    request_number: "",
    requester_user_ids: [],
    cost_center_codes: [],
    product_code: "",
    supplier_code: "",
    order_number: "",
    overall_stages: [],
    page: 1,
    page_size: 50,
    request: "",
  };
}

export function parseCsvValues(raw: string): string[] {
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function serializeCsvValues(ids: string[]): string {
  return ids.map((item) => item.trim()).filter(Boolean).join(",");
}

function readParam(params: URLSearchParams, key: string): string {
  return (params.get(key) ?? "").trim();
}

function readCsvOrRepeated(params: URLSearchParams, key: string, csvKey?: string): string[] {
  const repeated = params
    .getAll(key)
    .flatMap((item) => parseCsvValues(item));
  if (repeated.length > 0) return Array.from(new Set(repeated));
  if (csvKey) return Array.from(new Set(parseCsvValues(readParam(params, csvKey))));
  return [];
}

function readRequesterIds(params: URLSearchParams): string[] {
  const repeated = params
    .getAll("requester_user_id")
    .map((item) => item.trim())
    .filter(Boolean);
  if (repeated.length > 0) return repeated;
  return parseCsvValues(readParam(params, "requester"));
}

function readOverallStages(params: URLSearchParams): OverallStage[] {
  const allowed = new Set<string>(OVERALL_STAGE_VALUES);
  return readCsvOrRepeated(params, "overall_stage").filter((item): item is OverallStage =>
    allowed.has(item),
  );
}

function readInt(params: URLSearchParams, key: string, fallback: number): number {
  const raw = readParam(params, key);
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function parseUrlState(search: string, fallbackBranch: string): UrlState {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const defaults = createDefaultUrlState(fallbackBranch);
  return {
    branch: readParam(params, "branch") || defaults.branch,
    date_from: readParam(params, "date_from") || defaults.date_from,
    date_to: readParam(params, "date_to") || defaults.date_to,
    request_number: readParam(params, "request_number"),
    requester_user_ids: readRequesterIds(params),
    cost_center_codes: readCsvOrRepeated(params, "cost_center"),
    product_code: readParam(params, "product_code"),
    supplier_code: readParam(params, "supplier_code"),
    order_number: readParam(params, "order_number"),
    overall_stages: readOverallStages(params),
    page: readInt(params, "page", 1),
    page_size: readInt(params, "page_size", 50),
    request: readParam(params, "request"),
  };
}

export function buildUrlSearch(state: UrlState): string {
  const params = new URLSearchParams();
  if (state.branch) params.set("branch", state.branch);
  if (state.date_from) params.set("date_from", state.date_from);
  if (state.date_to) params.set("date_to", state.date_to);
  if (state.request_number) params.set("request_number", state.request_number);
  const requesters = serializeCsvValues(state.requester_user_ids);
  if (requesters) params.set("requester", requesters);
  const costCenters = serializeCsvValues(state.cost_center_codes);
  if (costCenters) params.set("cost_center", costCenters);
  if (state.product_code) params.set("product_code", state.product_code);
  if (state.supplier_code) params.set("supplier_code", state.supplier_code);
  if (state.order_number) params.set("order_number", state.order_number);
  const stages = serializeCsvValues(state.overall_stages);
  if (stages) params.set("overall_stage", stages);
  if (state.page > 1) params.set("page", String(state.page));
  if (state.page_size !== 50) params.set("page_size", String(state.page_size));
  if (state.request) params.set("request", state.request);
  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}

export function replaceUrlState(pathname: string, state: UrlState): void {
  if (typeof window === "undefined") return;
  const next = `${pathname || BASE_PATH}${buildUrlSearch(state)}`;
  const current = `${window.location.pathname}${window.location.search}`;
  if (next === current) return;
  window.history.replaceState(window.history.state, "", next);
}

export function queryFromUrlState(state: UrlState): PurchaseRequestsQuery {
  const { request: _request, ...query } = state;
  void _request;
  return query;
}

export function parseRequestKey(raw: string): { branch: string; requestNumber: string } | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const parts = trimmed.split(":");
  if (parts.length !== 2) return null;
  const branch = parts[0]?.trim();
  const requestNumber = parts[1]?.trim();
  if (!branch || !requestNumber) return null;
  return { branch, requestNumber };
}

export function buildRequestKey(branch: string, requestNumber: string): string {
  return `${branch}:${requestNumber}`;
}

export function searchHasExplicitFilters(search: string): boolean {
  const raw = search.startsWith("?") ? search.slice(1) : search;
  return new URLSearchParams(raw).toString().length > 0;
}
