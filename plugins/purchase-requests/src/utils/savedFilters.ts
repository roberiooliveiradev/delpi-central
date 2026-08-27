import type { OverallStage, PurchaseRequestsQuery } from "../types/purchaseRequests";
import { OVERALL_STAGE_VALUES } from "../types/purchaseRequests";
import {
  createDefaultUrlState,
  parseUrlState,
  searchHasExplicitFilters,
  type UrlState,
} from "./urlState";

export const SAVED_FILTERS_STORAGE_KEY = "purchase-requests:saved-filters:v1";

export type SavedPurchaseRequestsFilters = Pick<
  PurchaseRequestsQuery,
  | "branch"
  | "date_from"
  | "date_to"
  | "request_number"
  | "requester_user_ids"
  | "cost_center_codes"
  | "product_code"
  | "supplier_code"
  | "order_number"
  | "overall_stages"
>;

const STAGE_SET = new Set<string>(OVERALL_STAGE_VALUES);

function readStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function asStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  const result: string[] = [];
  for (const item of value) {
    const trimmed = String(item ?? "").trim();
    if (!trimmed || seen.has(trimmed)) continue;
    seen.add(trimmed);
    result.push(trimmed);
  }
  return result;
}

function asStages(value: unknown): OverallStage[] {
  return asStringList(value).filter((item): item is OverallStage => STAGE_SET.has(item));
}

function asText(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

export function snapshotSavedFilters(query: PurchaseRequestsQuery): SavedPurchaseRequestsFilters {
  return {
    branch: query.branch.trim(),
    date_from: query.date_from.trim(),
    date_to: query.date_to.trim(),
    request_number: query.request_number.trim(),
    requester_user_ids: asStringList(query.requester_user_ids),
    cost_center_codes: asStringList(query.cost_center_codes),
    product_code: query.product_code.trim(),
    supplier_code: query.supplier_code.trim(),
    order_number: query.order_number.trim(),
    overall_stages: asStages(query.overall_stages),
  };
}

export function parseSavedFilters(raw: unknown): SavedPurchaseRequestsFilters | null {
  if (!raw || typeof raw !== "object") return null;
  const record = raw as Record<string, unknown>;
  const snapshot = snapshotSavedFilters({
    branch: asText(record.branch),
    date_from: asText(record.date_from),
    date_to: asText(record.date_to),
    request_number: asText(record.request_number),
    requester_user_ids: asStringList(record.requester_user_ids),
    cost_center_codes: asStringList(record.cost_center_codes),
    product_code: asText(record.product_code),
    supplier_code: asText(record.supplier_code),
    order_number: asText(record.order_number),
    overall_stages: asStages(record.overall_stages),
    page: 1,
    page_size: 50,
  });
  return snapshot;
}

export function loadSavedFilters(): SavedPurchaseRequestsFilters | null {
  const storage = readStorage();
  if (!storage) return null;
  try {
    const raw = storage.getItem(SAVED_FILTERS_STORAGE_KEY);
    if (!raw) return null;
    return parseSavedFilters(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function persistSavedFilters(query: PurchaseRequestsQuery): SavedPurchaseRequestsFilters {
  const snapshot = snapshotSavedFilters(query);
  const storage = readStorage();
  if (storage) {
    storage.setItem(SAVED_FILTERS_STORAGE_KEY, JSON.stringify(snapshot));
  }
  return snapshot;
}

export function clearSavedFilters(): void {
  readStorage()?.removeItem(SAVED_FILTERS_STORAGE_KEY);
}

export function applySavedFilters(
  base: UrlState,
  saved: SavedPurchaseRequestsFilters | null,
): UrlState {
  if (!saved) return base;
  return {
    ...base,
    ...saved,
    branch: saved.branch || base.branch,
    page: 1,
    request: base.request,
  };
}

export function resolveInitialUrlState(search: string, fallbackBranch: string): UrlState {
  const parsed = parseUrlState(search, fallbackBranch);
  if (searchHasExplicitFilters(search)) return parsed;
  return applySavedFilters(createDefaultUrlState(fallbackBranch), loadSavedFilters());
}

export function areSavedFiltersEqual(
  left: SavedPurchaseRequestsFilters | null,
  right: SavedPurchaseRequestsFilters | null,
): boolean {
  if (left === right) return true;
  if (!left || !right) return false;
  return JSON.stringify(left) === JSON.stringify(right);
}
