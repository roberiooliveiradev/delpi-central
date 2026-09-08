/**
 * Sync query ↔ filtros do admin (plugin-mfe-page-excellence P0).
 * Keys em inglês; replaceState sem popstate (não remonta a rota).
 */

export type AdminAuditUrlFilters = {
  search: string;
  context: string;
  action: string;
  userId: string;
  traceId: string;
  dateFrom: string;
  dateTo: string;
};

export type AdminKnowledgeUrlFilters = {
  search: string;
  status: "all" | "active" | "inactive";
  category: string;
  namespace: string;
  domain: string;
  tag: string;
  sourceType: string;
};

export const DEFAULT_ADMIN_AUDIT_URL_FILTERS: AdminAuditUrlFilters = {
  search: "",
  context: "",
  action: "",
  userId: "",
  traceId: "",
  dateFrom: "",
  dateTo: "",
};

export const DEFAULT_ADMIN_KNOWLEDGE_URL_FILTERS: AdminKnowledgeUrlFilters = {
  search: "",
  status: "all",
  category: "",
  namespace: "",
  domain: "",
  tag: "",
  sourceType: "",
};

export const ADMIN_AUDIT_QUERY_KEYS = [
  "q",
  "context",
  "action",
  "userId",
  "traceId",
  "dateFrom",
  "dateTo",
] as const;

export const ADMIN_KNOWLEDGE_QUERY_KEYS = [
  "q",
  "status",
  "category",
  "namespace",
  "domain",
  "tag",
  "sourceType",
] as const;

export const ADMIN_METRICS_QUERY_KEYS = ["hours"] as const;

export const ADMIN_FILTER_QUERY_KEYS = Array.from(
  new Set<string>([
    ...ADMIN_AUDIT_QUERY_KEYS,
    ...ADMIN_KNOWLEDGE_QUERY_KEYS,
    ...ADMIN_METRICS_QUERY_KEYS,
  ]),
);

const ALLOWED_METRICS_HOURS = new Set([24, 168, 720]);

function readSearchParams(search?: string): URLSearchParams {
  if (typeof search === "string") {
    const normalized = search.startsWith("?") ? search.slice(1) : search;
    return new URLSearchParams(normalized);
  }

  if (typeof window !== "undefined") {
    return new URLSearchParams(window.location.search);
  }

  return new URLSearchParams();
}

export function parseAuditFiltersFromSearch(search?: string): AdminAuditUrlFilters {
  const params = readSearchParams(search);
  return {
    search: params.get("q")?.trim() ?? "",
    context: params.get("context")?.trim() ?? "",
    action: params.get("action")?.trim() ?? "",
    userId: params.get("userId")?.trim() ?? "",
    traceId: params.get("traceId")?.trim() ?? "",
    dateFrom: params.get("dateFrom")?.trim() ?? "",
    dateTo: params.get("dateTo")?.trim() ?? "",
  };
}

export function serializeAuditFiltersToQuery(
  filters: AdminAuditUrlFilters,
): Record<string, string | null> {
  return {
    q: filters.search.trim() || null,
    context: filters.context.trim() || null,
    action: filters.action.trim() || null,
    userId: filters.userId.trim() || null,
    traceId: filters.traceId.trim() || null,
    dateFrom: filters.dateFrom.trim() || null,
    dateTo: filters.dateTo.trim() || null,
  };
}

function parseDocumentStatus(value: string | null): AdminKnowledgeUrlFilters["status"] {
  if (value === "active" || value === "inactive" || value === "all") {
    return value;
  }
  return "all";
}

export function parseKnowledgeFiltersFromSearch(
  search?: string,
): AdminKnowledgeUrlFilters {
  const params = readSearchParams(search);
  return {
    search: params.get("q")?.trim() ?? "",
    status: parseDocumentStatus(params.get("status")),
    category: params.get("category")?.trim() ?? "",
    namespace: params.get("namespace")?.trim() ?? "",
    domain: params.get("domain")?.trim() ?? "",
    tag: params.get("tag")?.trim() ?? "",
    sourceType: params.get("sourceType")?.trim() ?? "",
  };
}

export function serializeKnowledgeFiltersToQuery(
  filters: AdminKnowledgeUrlFilters,
): Record<string, string | null> {
  return {
    q: filters.search.trim() || null,
    status: filters.status !== "all" ? filters.status : null,
    category: filters.category.trim() || null,
    namespace: filters.namespace.trim() || null,
    domain: filters.domain.trim() || null,
    tag: filters.tag.trim() || null,
    sourceType: filters.sourceType.trim() || null,
  };
}

export function parseMetricsHoursFromSearch(search?: string, fallback = 24): number {
  const raw = readSearchParams(search).get("hours");
  const hours = raw ? Number(raw) : fallback;
  if (!Number.isFinite(hours) || !ALLOWED_METRICS_HOURS.has(hours)) {
    return fallback;
  }
  return hours;
}

export function serializeMetricsHoursToQuery(hours: number): Record<string, string | null> {
  if (hours === 24 || !ALLOWED_METRICS_HOURS.has(hours)) {
    return { hours: null };
  }
  return { hours: String(hours) };
}

/**
 * Atualiza a query atual com patch (null/"" remove a key).
 * Não dispara popstate — evita remount destrutivo.
 */
export function replaceAdminUrlSearch(
  patch: Record<string, string | null | undefined>,
  options?: { removeKeys?: readonly string[] },
): void {
  if (typeof window === "undefined") {
    return;
  }

  const url = new URL(window.location.href);

  for (const key of options?.removeKeys ?? []) {
    url.searchParams.delete(key);
  }

  for (const [key, value] of Object.entries(patch)) {
    if (value == null || value === "") {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, value);
    }
  }

  const next = `${url.pathname}${url.search}${url.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (next === current) {
    return;
  }

  window.history.replaceState(window.history.state, "", next);
}

export function clearAdminFilterQuery(): void {
  replaceAdminUrlSearch({}, { removeKeys: ADMIN_FILTER_QUERY_KEYS });
}

export function syncAuditFiltersToUrl(filters: AdminAuditUrlFilters): void {
  replaceAdminUrlSearch(serializeAuditFiltersToQuery(filters));
}

export function syncKnowledgeFiltersToUrl(filters: AdminKnowledgeUrlFilters): void {
  replaceAdminUrlSearch(serializeKnowledgeFiltersToQuery(filters));
}

export function syncMetricsHoursToUrl(hours: number): void {
  replaceAdminUrlSearch(serializeMetricsHoursToQuery(hours));
}

/** Path canônico + search/hash atuais (rewrite EN sem apagar filtros). */
export function withCurrentAdminSearch(pathname: string): string {
  if (typeof window === "undefined") {
    return pathname;
  }
  return `${pathname}${window.location.search}${window.location.hash}`;
}
