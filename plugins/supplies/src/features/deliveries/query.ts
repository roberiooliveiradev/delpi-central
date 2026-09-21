import {
  canonicalizeUiBranches,
  normalizeSuppliesUnitCode,
} from "../../app/suppliesUnits";
import { resolvePeriodPreset } from "../../app/periodPreset";
import type {
  DeliveriesQuery,
  DeliveriesSortDir,
  DeliveryPunctualityStatus,
} from "./types";
import { DEFAULT_PAGE_SIZE } from "./types";

/** Column key (UI) → BFF sort_by (producer allow-list). */
export const DELIVERIES_SORTABLE_COLUMNS = {
  branch: "branch",
  order_number: "order_number",
  order_item: "order_item",
  supplier: "supplier_name",
  product: "product_description",
  quantity: "quantity",
  expected_delivery_date: "expected_delivery_date",
  receipt_entry_date: "receipt_entry_date",
  days_diff: "days_diff",
  status: "status",
} as const;

export type DeliverySortableColumnKey = keyof typeof DELIVERIES_SORTABLE_COLUMNS;

function currentMonthRange(now: Date = new Date()): { from: string; to: string } {
  const range = resolvePeriodPreset("this_month", now);
  return {
    from: range?.from ?? "",
    to: range?.to ?? "",
  };
}

export function createDefaultQuery(
  _branches: readonly string[] = [],
  now: Date = new Date(),
): DeliveriesQuery {
  const month = currentMonthRange(now);
  return {
    branches: [],
    status: "late",
    start_date: month.from,
    end_date: month.to,
    sort_by: "",
    sort_dir: "asc",
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
  };
}

function readParam(params: URLSearchParams, key: string): string {
  return (params.get(key) || "").trim();
}

function readInt(params: URLSearchParams, key: string, fallback: number): number {
  const raw = readParam(params, key);
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function readSortDir(raw: string): DeliveriesSortDir {
  return raw === "desc" ? "desc" : "asc";
}

function readStatus(raw: string): DeliveryPunctualityStatus {
  return raw === "on_time" ? "on_time" : "late";
}

function readSortBy(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";
  const allowed = Object.values(DELIVERIES_SORTABLE_COLUMNS) as readonly string[];
  return allowed.includes(trimmed) ? trimmed : "";
}

export function parseQueryFromSearch(
  search: string,
  allowedUnits: readonly string[] = [],
  now: Date = new Date(),
): DeliveriesQuery {
  const defaults = createDefaultQuery([], now);
  const params = new URLSearchParams(
    search.startsWith("?") ? search.slice(1) : search,
  );
  const branchesRaw = params.getAll("branch").map((b) => b.trim()).filter(Boolean);
  const branches = canonicalizeUiBranches(branchesRaw, allowedUnits);

  const start = readParam(params, "start_date") || defaults.start_date;
  const end = readParam(params, "end_date") || defaults.end_date;

  return {
    branches,
    status: readStatus(readParam(params, "status")),
    start_date: start,
    end_date: end,
    sort_by: readSortBy(readParam(params, "sort_by")),
    sort_dir: readSortDir(readParam(params, "sort_dir")),
    page: readInt(params, "page", 1),
    page_size: readInt(params, "page_size", DEFAULT_PAGE_SIZE),
  };
}

export function sameDeliveriesQuery(
  left: DeliveriesQuery,
  right: DeliveriesQuery,
): boolean {
  if (left.status !== right.status) return false;
  if (left.start_date !== right.start_date) return false;
  if (left.end_date !== right.end_date) return false;
  if (left.sort_by !== right.sort_by) return false;
  if (left.sort_dir !== right.sort_dir) return false;
  if (left.page !== right.page) return false;
  if (left.page_size !== right.page_size) return false;
  if (left.branches.length !== right.branches.length) return false;
  return left.branches.every((code, index) => code === right.branches[index]);
}

/**
 * BFF query builder.
 * Empty branches = «Todas» → omit `branch` (BFF composes 01+02).
 * Never emit branch=all / consolidated / dual append for Todas.
 */
export function buildListSearchParams(
  query: DeliveriesQuery,
  options?: { includePagination?: boolean },
): URLSearchParams {
  const params = new URLSearchParams();
  for (const branch of query.branches) {
    const code = normalizeSuppliesUnitCode(branch);
    if (code) params.append("branch", code);
  }
  params.set("status", query.status === "on_time" ? "on_time" : "late");
  if (query.start_date.trim()) params.set("start_date", query.start_date.trim());
  if (query.end_date.trim()) params.set("end_date", query.end_date.trim());
  if (query.sort_by.trim()) {
    params.set("sort_by", query.sort_by.trim());
    params.set("sort_dir", query.sort_dir === "desc" ? "desc" : "asc");
  }
  if (options?.includePagination !== false) {
    params.set("page", String(query.page));
    params.set("page_size", String(query.page_size));
  }
  return params;
}

export function buildUrlSearch(query: DeliveriesQuery): string {
  const params = buildListSearchParams(query);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function nextServerSort(
  current: DeliveriesQuery,
  columnKey: string,
): Pick<DeliveriesQuery, "sort_by" | "sort_dir" | "page"> | null {
  const sortBy =
    DELIVERIES_SORTABLE_COLUMNS[columnKey as DeliverySortableColumnKey];
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
  const entry = Object.entries(DELIVERIES_SORTABLE_COLUMNS).find(
    ([, field]) => field === sortBy,
  );
  return entry?.[0] ?? null;
}

export function formatDatePtBr(iso: string | null | undefined): string {
  if (!iso) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function labelDeliveryStatus(status: string | null | undefined): string {
  switch (status) {
    case "late":
      return "Em atraso";
    case "on_time":
      return "No prazo";
    default:
      return status || "—";
  }
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

export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
}

export function formatDaysDiff(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}
