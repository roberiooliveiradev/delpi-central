import type {
  SafetyStockBranchScope,
  SafetyStockDetailTarget,
  SafetyStockQuery,
  SafetyStockSortDirection,
  SafetyStockSortField,
  SafetyStockStatus,
} from "./types";
import {
  DEFAULT_PAGE_SIZE,
  DEFAULT_SAFETY_STOCK_SORT_DIRECTION,
  DEFAULT_SAFETY_STOCK_SORT_FIELD,
  MAX_PAGE_SIZE,
  SAFETY_STOCK_ALL_SCOPE,
  SAFETY_STOCK_BRANCH_SCOPES,
  SAFETY_STOCK_SORT_FIELDS,
  SAFETY_STOCK_STATUSES,
} from "./types";

export function createDefaultQuery(): SafetyStockQuery {
  return {
    branch: SAFETY_STOCK_ALL_SCOPE,
    status: "",
    productGroup: "",
    unit: "",
    search: "",
    includeBlocked: false,
    includeWithoutSafetyStock: true,
    sortBy: DEFAULT_SAFETY_STOCK_SORT_FIELD,
    sortDirection: DEFAULT_SAFETY_STOCK_SORT_DIRECTION,
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
  };
}

function readParam(params: URLSearchParams, key: string): string {
  return (params.get(key) || "").trim();
}

function readInt(
  params: URLSearchParams,
  key: string,
  fallback: number,
  max?: number,
): number {
  const raw = readParam(params, key);
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return fallback;
  if (max !== undefined && n > max) return fallback;
  return n;
}

function readBool(
  params: URLSearchParams,
  key: string,
  fallback: boolean,
): boolean {
  const raw = readParam(params, key).toLowerCase();
  if (!raw) return fallback;
  if (raw === "true" || raw === "1") return true;
  if (raw === "false" || raw === "0") return false;
  return fallback;
}

/** Escopo desconhecido na URL recupera para «all» (nunca quebra o deep link). */
export function normalizeBranchScope(
  raw: string | null | undefined,
): SafetyStockBranchScope {
  const trimmed = String(raw ?? "").trim();
  if ((SAFETY_STOCK_BRANCH_SCOPES as readonly string[]).includes(trimmed)) {
    return trimmed as SafetyStockBranchScope;
  }
  return SAFETY_STOCK_ALL_SCOPE;
}

export function normalizeStatus(raw: string | null | undefined): SafetyStockStatus | "" {
  const trimmed = String(raw ?? "").trim();
  if ((SAFETY_STOCK_STATUSES as readonly string[]).includes(trimmed)) {
    return trimmed as SafetyStockStatus;
  }
  return "";
}

export function normalizeSortField(
  raw: string | null | undefined,
): SafetyStockSortField {
  const trimmed = String(raw ?? "").trim();
  if ((SAFETY_STOCK_SORT_FIELDS as readonly string[]).includes(trimmed)) {
    return trimmed as SafetyStockSortField;
  }
  return DEFAULT_SAFETY_STOCK_SORT_FIELD;
}

export function normalizeSortDirection(
  raw: string | null | undefined,
): SafetyStockSortDirection {
  const trimmed = String(raw ?? "").trim().toLowerCase();
  return trimmed === "desc" ? "desc" : DEFAULT_SAFETY_STOCK_SORT_DIRECTION;
}

export function parseQueryFromSearch(search: string): SafetyStockQuery {
  const params = new URLSearchParams(
    search.startsWith("?") ? search.slice(1) : search,
  );
  return {
    branch: normalizeBranchScope(readParam(params, "branch")),
    status: normalizeStatus(readParam(params, "status")),
    productGroup: readParam(params, "productGroup"),
    unit: readParam(params, "unit"),
    search: readParam(params, "search"),
    includeBlocked: readBool(params, "includeBlocked", false),
    includeWithoutSafetyStock: readBool(
      params,
      "includeWithoutSafetyStock",
      true,
    ),
    sortBy: normalizeSortField(readParam(params, "sortBy")),
    sortDirection: normalizeSortDirection(readParam(params, "sortDirection")),
    page: readInt(params, "page", 1),
    page_size: readInt(params, "page_size", DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE),
  };
}

export function sameSafetyStockQuery(
  left: SafetyStockQuery,
  right: SafetyStockQuery,
): boolean {
  return (
    left.branch === right.branch &&
    left.status === right.status &&
    left.productGroup === right.productGroup &&
    left.unit === right.unit &&
    left.search === right.search &&
    left.includeBlocked === right.includeBlocked &&
    left.includeWithoutSafetyStock === right.includeWithoutSafetyStock &&
    left.sortBy === right.sortBy &&
    left.sortDirection === right.sortDirection &&
    left.page === right.page &&
    left.page_size === right.page_size
  );
}

/**
 * Filtros compartilhados por summary/items (sem paginação nem sort).
 * `branch=all` é enviado como escopo único — o BFF repassa uma consulta
 * consolidada ao produtor (sem fan-out).
 */
export function buildScopeFilterParams(
  query: Pick<
    SafetyStockQuery,
    | "branch"
    | "status"
    | "productGroup"
    | "unit"
    | "search"
    | "includeBlocked"
    | "includeWithoutSafetyStock"
  >,
): URLSearchParams {
  const params = new URLSearchParams();
  params.set("branch", normalizeBranchScope(query.branch));
  if (query.status) params.set("status", query.status);
  if (query.productGroup.trim()) {
    params.set("productGroup", query.productGroup.trim());
  }
  if (query.unit.trim()) params.set("unit", query.unit.trim());
  if (query.search.trim()) params.set("search", query.search.trim());
  params.set("includeBlocked", query.includeBlocked ? "true" : "false");
  params.set(
    "includeWithoutSafetyStock",
    query.includeWithoutSafetyStock ? "true" : "false",
  );
  return params;
}

export function buildItemsSearchParams(query: SafetyStockQuery): URLSearchParams {
  const params = buildScopeFilterParams(query);
  params.set("page", String(query.page));
  params.set("page_size", String(query.page_size));
  params.set("sortBy", normalizeSortField(query.sortBy));
  params.set("sortDirection", normalizeSortDirection(query.sortDirection));
  return params;
}

export function buildUrlSearch(query: SafetyStockQuery): string {
  const defaults = createDefaultQuery();
  const params = new URLSearchParams();
  if (query.branch !== defaults.branch) params.set("branch", query.branch);
  if (query.status) params.set("status", query.status);
  if (query.productGroup.trim()) {
    params.set("productGroup", query.productGroup.trim());
  }
  if (query.unit.trim()) params.set("unit", query.unit.trim());
  if (query.search.trim()) params.set("search", query.search.trim());
  if (query.includeBlocked !== defaults.includeBlocked) {
    params.set("includeBlocked", "true");
  }
  if (query.includeWithoutSafetyStock !== defaults.includeWithoutSafetyStock) {
    params.set("includeWithoutSafetyStock", "false");
  }
  params.set("sortBy", normalizeSortField(query.sortBy));
  params.set("sortDirection", normalizeSortDirection(query.sortDirection));
  params.set("page", String(query.page));
  params.set("page_size", String(query.page_size));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

/**
 * E11.S3 — deep links legados (`item` + `itemBranch` na query) redirecionam
 * para a rota canônica de detalhe. Filial concreta obrigatória:
 * `all`/vazio/inválido → null (não abre).
 */
export function parseDetailTargetFromSearch(
  search: string,
): SafetyStockDetailTarget | null {
  const params = new URLSearchParams(
    search.startsWith("?") ? search.slice(1) : search,
  );
  const productCode = readParam(params, "item").trim();
  const branch = normalizeBranchScope(readParam(params, "itemBranch"));
  if (!productCode || branch === SAFETY_STOCK_ALL_SCOPE) return null;
  return { productCode, branch };
}

/** Campos numéricos abrem em desc; campos textuais/classificação em asc. */
const DESC_FIRST_COLUMNS = new Set<SafetyStockSortField>([
  "safety_stock",
  "primary_stock",
  "work_in_process_stock",
  "deficit_quantity",
]);

export function nextServerSort(
  current: SafetyStockQuery,
  columnKey: string,
): Pick<SafetyStockQuery, "sortBy" | "sortDirection" | "page"> | null {
  if (!(SAFETY_STOCK_SORT_FIELDS as readonly string[]).includes(columnKey)) {
    return null;
  }
  const field = columnKey as SafetyStockSortField;
  if (current.sortBy === field) {
    return {
      sortBy: field,
      sortDirection: current.sortDirection === "asc" ? "desc" : "asc",
      page: 1,
    };
  }
  return {
    sortBy: field,
    sortDirection: DESC_FIRST_COLUMNS.has(field) ? "desc" : "asc",
    page: 1,
  };
}

export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
}

export function formatUnitOfMeasure(value: string | null | undefined): string {
  const trimmed = String(value ?? "").trim();
  return trimmed || "—";
}

/* E11.S3 — helpers de apresentação do detalhe. */

export function formatDatePtBr(iso: string | null | undefined): string {
  if (!iso) return "—";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function formatCurrencyPtBr(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
