import { useCallback, useEffect, useState } from "react";

import type { RequestListFiltersState } from "../content/requestListFilters";
import { navigateMyRequestsPath } from "./myRequestsNavigation";

const MINE_SCOPES = new Set(["", "completed_by_me", "assigned_to_me"]);

/** Serializa filtros para query string (apenas valores não-default). */
export function requestListFiltersToSearch(
  filters: RequestListFiltersState,
): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.typeCode) params.set("type", filters.typeCode);
  if (filters.status) params.set("status", filters.status);
  if (filters.branch) params.set("branch", filters.branch);
  if (filters.mineScope) params.set("mine_scope", filters.mineScope);
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.page > 1) params.set("page", String(filters.page));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

/** Query string → filtros (campos ausentes herdam o default da página). */
export function requestListFiltersFromSearch(
  search: string,
  defaults: RequestListFiltersState,
): RequestListFiltersState {
  const params = new URLSearchParams(search || "");
  const scope = params.get("mine_scope") ?? "";
  const page = Number.parseInt(params.get("page") || "1", 10);
  return {
    ...defaults,
    q: params.get("q") ?? defaults.q,
    typeCode: params.get("type") ?? defaults.typeCode,
    status: params.get("status") ?? defaults.status,
    branch: params.get("branch") ?? defaults.branch,
    mineScope: MINE_SCOPES.has(scope)
      ? (scope as RequestListFiltersState["mineScope"])
      : defaults.mineScope,
    sort: params.get("sort") ?? defaults.sort,
    page: Number.isFinite(page) && page > 0 ? page : 1,
  };
}

/**
 * Estado de listagem persistido na URL — deep link, refresh e
 * back/forward preservam busca, filtros, ordenação e página.
 * Commits usam replaceState (sem poluir o histórico por tecla).
 */
export function useRequestListUrlState(
  defaults: RequestListFiltersState,
): [
  RequestListFiltersState,
  (patch: Partial<RequestListFiltersState>) => void,
  (next: RequestListFiltersState) => void,
] {
  const [filters, setFilters] = useState<RequestListFiltersState>(() =>
    typeof window === "undefined"
      ? defaults
      : requestListFiltersFromSearch(window.location.search, defaults),
  );

  // Back/forward: URL muda fora do commit → reparse.
  useEffect(() => {
    const onPopState = () =>
      setFilters((prev) => {
        const next = requestListFiltersFromSearch(
          window.location.search,
          defaults,
        );
        return JSON.stringify(prev) === JSON.stringify(next) ? prev : next;
      });
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
    // defaults é constante por página
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const syncUrl = useCallback((merged: RequestListFiltersState) => {
    if (typeof window === "undefined") return;
    navigateMyRequestsPath(
      `${window.location.pathname}${requestListFiltersToSearch(merged)}`,
      { replace: true },
    );
  }, []);

  const patchFilters = useCallback(
    (patch: Partial<RequestListFiltersState>) => {
      setFilters((prev) => {
        const merged = { ...prev, ...patch };
        syncUrl(merged);
        return merged;
      });
    },
    [syncUrl],
  );

  const setAll = useCallback(
    (next: RequestListFiltersState) => {
      syncUrl(next);
      setFilters(next);
    },
    [syncUrl],
  );

  return [filters, patchFilters, setAll];
}
