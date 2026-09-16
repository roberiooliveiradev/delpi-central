import {
  canonicalizeUiBranches,
  normalizeSuppliesUnitCode,
  resolveRequestedBranches,
} from "../../app/suppliesUnits";
import type { PurchaseOrdersQuery, PurchaseOrdersSortDir } from "./types";
import { DEFAULT_PAGE_SIZE } from "./types";

export const PURCHASE_ORDERS_SORTABLE_COLUMNS = {
  order_number: "order_number",
  order_item: "order_item",
  product: "product_description",
  supplier: "supplier_name",
  open_quantity: "open_quantity",
  delivery: "expected_delivery_date",
  status: "delivery_status",
  open_value: "open_value",
} as const;

export type PurchaseOrderSortableColumnKey = keyof typeof PURCHASE_ORDERS_SORTABLE_COLUMNS;

/** UI default: empty branches = «Todas» (API expands via authorizeQueryBranches). */
export function createDefaultQuery(
  _branches: readonly string[] = [],
): PurchaseOrdersQuery {
  return {
    branches: [],
    order_number: "",
    product_code: "",
    supplier_code: "",
    expected_delivery_from: "",
    expected_delivery_to: "",
    late_only: false,
    sort_by: "",
    sort_dir: "asc",
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    order: "",
  };
}

export function buildListSearchParams(
  query: PurchaseOrdersQuery,
  options?: { includePagination?: boolean },
): URLSearchParams {
  const params = new URLSearchParams();
  for (const branch of query.branches) {
    const code = normalizeSuppliesUnitCode(branch);
    if (code) params.append("branch", code);
  }
  if (query.order_number.trim()) params.set("order_number", query.order_number.trim());
  if (query.product_code.trim()) params.set("product_code", query.product_code.trim());
  if (query.supplier_code.trim()) params.set("supplier_code", query.supplier_code.trim());
  if (query.expected_delivery_from.trim()) {
    params.set("expected_delivery_from", query.expected_delivery_from.trim());
  }
  if (query.expected_delivery_to.trim()) {
    params.set("expected_delivery_to", query.expected_delivery_to.trim());
  }
  if (query.late_only) params.set("late_only", "true");
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

export function buildOrderKey(branch: string, orderNumber: string): string {
  return `${branch}:${orderNumber}`;
}

export function parseOrderKey(raw: string): { branch: string; orderNumber: string } | null {
  const trimmed = raw.trim();
  if (!trimmed.includes(":")) return null;
  const [branch, ...rest] = trimmed.split(":");
  const orderNumber = rest.join(":").trim();
  if (!branch?.trim() || !orderNumber) return null;
  return { branch: branch.trim(), orderNumber };
}

function readParam(params: URLSearchParams, key: string): string {
  return (params.get(key) ?? "").trim();
}

function readInt(params: URLSearchParams, key: string, fallback: number): number {
  const parsed = Number.parseInt(readParam(params, key), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function readSortDir(raw: string): PurchaseOrdersSortDir {
  return raw.toLowerCase() === "desc" ? "desc" : "asc";
}

export function parseQueryFromSearch(
  search: string,
  allowedUnits: readonly string[] = [],
): PurchaseOrdersQuery {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const lateRaw = readParam(params, "late_only").toLowerCase();
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
    order_number: readParam(params, "order_number"),
    product_code: readParam(params, "product_code"),
    supplier_code: readParam(params, "supplier_code"),
    expected_delivery_from: readParam(params, "expected_delivery_from"),
    expected_delivery_to: readParam(params, "expected_delivery_to"),
    late_only: lateRaw === "1" || lateRaw === "true" || lateRaw === "yes",
    sort_by: readParam(params, "sort_by"),
    sort_dir: readSortDir(readParam(params, "sort_dir")),
    page: readInt(params, "page", 1),
    page_size: readInt(params, "page_size", DEFAULT_PAGE_SIZE),
    order: readParam(params, "order"),
  };
}

export function buildUrlSearch(query: PurchaseOrdersQuery): string {
  const params = buildListSearchParams(query);
  if (query.order.trim()) params.set("order", query.order.trim());
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function nextServerSort(
  current: PurchaseOrdersQuery,
  columnKey: string,
): Pick<PurchaseOrdersQuery, "sort_by" | "sort_dir" | "page"> | null {
  const sortBy =
    PURCHASE_ORDERS_SORTABLE_COLUMNS[columnKey as PurchaseOrderSortableColumnKey];
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
  const entry = Object.entries(PURCHASE_ORDERS_SORTABLE_COLUMNS).find(
    ([, field]) => field === sortBy,
  );
  return entry?.[0] ?? null;
}

export function authorizeQueryBranches(
  query: PurchaseOrdersQuery,
  allowedUnits: readonly string[],
): PurchaseOrdersQuery {
  return {
    ...query,
    branches: resolveRequestedBranches(query.branches, allowedUnits),
  };
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
      return "Atrasado";
    case "on_time":
      return "No prazo";
    case "no_date":
      return "Sem data";
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

export function formatMoneyBr(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  });
}

export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
}
