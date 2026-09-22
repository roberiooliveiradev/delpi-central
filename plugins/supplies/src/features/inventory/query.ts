import {
  canonicalizeUiBranches,
  normalizeSuppliesUnitCode,
} from "../../app/suppliesUnits";
import type {
  InventoryByWarehouse,
  InventoryQuery,
  InventorySort,
  InventorySortableColumnKey,
} from "./types";
import {
  DEFAULT_INVENTORY_SORT,
  DEFAULT_PAGE_SIZE,
  INVENTORY_ALLOWED_SORT,
  INVENTORY_SORTABLE_COLUMNS,
} from "./types";
import { INVENTORY_CONTENT as C } from "./content";

export function createDefaultQuery(): InventoryQuery {
  return {
    branches: [],
    warehouse: "",
    sort: DEFAULT_INVENTORY_SORT,
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

export function normalizeInventorySort(raw: string | null | undefined): InventorySort {
  const trimmed = String(raw ?? "").trim();
  if ((INVENTORY_ALLOWED_SORT as readonly string[]).includes(trimmed)) {
    return trimmed as InventorySort;
  }
  return DEFAULT_INVENTORY_SORT;
}

export function parseQueryFromSearch(
  search: string,
  allowedUnits: readonly string[] = [],
): InventoryQuery {
  const params = new URLSearchParams(
    search.startsWith("?") ? search.slice(1) : search,
  );
  const branchesRaw = params.getAll("branch").map((b) => b.trim()).filter(Boolean);
  const branches = canonicalizeUiBranches(branchesRaw, allowedUnits);
  const warehouse = readParam(params, "warehouse");

  return {
    branches,
    warehouse,
    sort: normalizeInventorySort(readParam(params, "sort")),
    page: readInt(params, "page", 1),
    page_size: readInt(params, "page_size", DEFAULT_PAGE_SIZE),
  };
}

export function sameInventoryQuery(
  left: InventoryQuery,
  right: InventoryQuery,
): boolean {
  if (left.warehouse !== right.warehouse) return false;
  if (left.sort !== right.sort) return false;
  if (left.page !== right.page) return false;
  if (left.page_size !== right.page_size) return false;
  if (left.branches.length !== right.branches.length) return false;
  return left.branches.every((code, index) => code === right.branches[index]);
}

/**
 * Empty branches = «Todas» → omit `branch` (BFF expands 01+02).
 * Never emit branch=all or force positive-only filters from the browser.
 */
export function buildBranchParams(branches: readonly string[]): URLSearchParams {
  const params = new URLSearchParams();
  for (const branch of branches) {
    const code = normalizeSuppliesUnitCode(branch);
    if (code) params.append("branch", code);
  }
  return params;
}

export function buildSummarySearchParams(
  query: Pick<InventoryQuery, "branches" | "warehouse">,
  options?: { includeWarehouse?: boolean },
): URLSearchParams {
  const params = buildBranchParams(query.branches);
  const includeWarehouse = options?.includeWarehouse !== false;
  if (includeWarehouse && query.warehouse.trim()) {
    params.set("warehouse", query.warehouse.trim());
  }
  return params;
}

export function buildItemsSearchParams(query: InventoryQuery): URLSearchParams {
  const params = buildSummarySearchParams(query);
  params.set("sort", normalizeInventorySort(query.sort));
  params.set("page", String(query.page));
  params.set("page_size", String(query.page_size));
  return params;
}

export function buildUrlSearch(query: InventoryQuery): string {
  const params = buildItemsSearchParams(query);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function parseSortToken(
  sort: InventorySort,
): { column: InventorySortableColumnKey; dir: "asc" | "desc" } {
  if (sort.startsWith("quantity_")) {
    return { column: "quantity", dir: sort.endsWith("_desc") ? "desc" : "asc" };
  }
  if (sort.startsWith("product_code_")) {
    return {
      column: "product_code",
      dir: sort.endsWith("_desc") ? "desc" : "asc",
    };
  }
  return {
    column: "stock_value",
    dir: sort.endsWith("_asc") ? "asc" : "desc",
  };
}

export function composeSortToken(
  column: InventorySortableColumnKey,
  dir: "asc" | "desc",
): InventorySort {
  const field = INVENTORY_SORTABLE_COLUMNS[column];
  return normalizeInventorySort(`${field}_${dir}`);
}

export function nextServerSort(
  current: InventoryQuery,
  columnKey: string,
): Pick<InventoryQuery, "sort" | "page"> | null {
  const field =
    INVENTORY_SORTABLE_COLUMNS[columnKey as InventorySortableColumnKey];
  if (!field) return null;
  const currentParsed = parseSortToken(current.sort);
  if (currentParsed.column === columnKey) {
    const nextDir = currentParsed.dir === "asc" ? "desc" : "asc";
    return {
      sort: composeSortToken(columnKey as InventorySortableColumnKey, nextDir),
      page: 1,
    };
  }
  return {
    sort: composeSortToken(columnKey as InventorySortableColumnKey, "desc"),
    page: 1,
  };
}

export function tableSortKey(sort: InventorySort): string {
  return parseSortToken(sort).column;
}

export function tableSortDirection(sort: InventorySort): "asc" | "desc" {
  return parseSortToken(sort).dir;
}

export function formatMoneyBr(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  });
}

/** Preserve sign for zero and negative balances. */
export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
}

export function formatUnitOfMeasure(value: string | null | undefined): string {
  const trimmed = String(value ?? "").trim();
  return trimmed || "—";
}

export function formatWarehouseDisplay(
  warehouse: string | null | undefined,
  warehouseLabel: string | null | undefined,
): string {
  const code = String(warehouse ?? "");
  if (!code.trim()) return C.warehouseCodeEmpty;
  const label = String(warehouseLabel ?? "").trim();
  if (label) return `${code.trim()} — ${label}`;
  return code.trim();
}

/**
 * Warehouse filter options from server-owned by_warehouse.
 * Identity = warehouse code. Empty codes are skipped as filter options
 * (FILTER_EMPTY_WAREHOUSE residual) but still render in the table under «Todos».
 */
export function buildWarehouseFilterOptions(
  rows: readonly InventoryByWarehouse[],
): { value: string; label: string }[] {
  const byCode = new Map<string, string>();
  for (const row of rows) {
    const code = String(row.warehouse ?? "").trim();
    if (!code) continue;
    if (byCode.has(code)) continue;
    const label = String(row.warehouse_label ?? "").trim();
    byCode.set(code, label ? `${code} — ${label}` : code);
  }
  return [...byCode.entries()]
    .sort(([a], [b]) => a.localeCompare(b, "pt-BR", { numeric: true }))
    .map(([value, label]) => ({ value, label }));
}
