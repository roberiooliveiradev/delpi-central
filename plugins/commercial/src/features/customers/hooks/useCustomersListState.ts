import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  buildCustomersListPath,
  buildCustomersListSearch,
  DEFAULT_CUSTOMERS_LIST_DIRECTION,
  DEFAULT_CUSTOMERS_LIST_SORT,
  parseCustomersListDeepLink,
  type CustomersListDeepLink,
  type CustomersListSellerAccess,
} from "../../../utils/customersListDeepLink";
import type { CustomerAttentionFilter, CustomerListSortKey } from "../types/customerSummary";

export type CustomersListState = CustomersListDeepLink;

export function updateCustomersListState(
  current: CustomersListState,
  change: Partial<CustomersListState>,
): CustomersListState {
  const resetsPage =
    change.q !== undefined ||
    change.focus !== undefined ||
    change.sellerId !== undefined ||
    change.sort !== undefined;
  return { ...current, ...change, page: change.page ?? (resetsPage ? 1 : current.page) };
}

const DEFAULT_STATE: CustomersListState = {
  q: "",
  focus: "all",
  sellerId: null,
  sort: DEFAULT_CUSTOMERS_LIST_SORT,
  dir: DEFAULT_CUSTOMERS_LIST_DIRECTION,
  page: 1,
};

export function useCustomersListState(options: {
  basePath: string;
  scopeLoading: boolean;
  sellerAccess: CustomersListSellerAccess;
  sellerAccessKey: string;
  sellerId: string | null;
  setSellerId: (sellerId: string | null) => void;
}) {
  const {
    basePath,
    scopeLoading,
    sellerAccess,
    sellerAccessKey,
    sellerId,
    setSellerId: setScopeSellerId,
  } = options;
  const [state, setState] = useState<CustomersListState>(DEFAULT_STATE);
  const hydratedAccessKeyRef = useRef<string | null>(null);

  useEffect(() => {
    if (scopeLoading || typeof window === "undefined") return;
    const applyBrowserState = () => {
      const next = parseCustomersListDeepLink(window.location.search, sellerAccess);
      setState(next);
      setScopeSellerId(next.sellerId);
      const canonicalPath = buildCustomersListPath(basePath, next, sellerAccess);
      const currentPath = `${window.location.pathname}${window.location.search}`;
      if (canonicalPath !== currentPath) {
        window.history.replaceState(window.history.state, "", canonicalPath);
      }
    };
    applyBrowserState();
    hydratedAccessKeyRef.current = sellerAccessKey;
    window.addEventListener("popstate", applyBrowserState);
    return () => window.removeEventListener("popstate", applyBrowserState);
  }, [basePath, scopeLoading, sellerAccess, sellerAccessKey, setScopeSellerId]);

  useEffect(() => {
    if (
      scopeLoading ||
      typeof window === "undefined" ||
      hydratedAccessKeyRef.current !== sellerAccessKey
    ) return;
    const target = buildCustomersListPath(basePath, { ...state, sellerId }, sellerAccess);
    const current = `${window.location.pathname}${window.location.search}`;
    if (target !== current) window.history.replaceState(window.history.state, "", target);
  }, [basePath, scopeLoading, sellerAccess, sellerAccessKey, sellerId, state]);

  const mutate = useCallback((change: Partial<CustomersListState>) => {
    setState((current) => updateCustomersListState(current, change));
  }, []);
  const setSearch = useCallback((q: string) => mutate({ q }), [mutate]);
  const setFilter = useCallback(
    (focus: CustomerAttentionFilter) => mutate({ focus }),
    [mutate],
  );
  const setSellerId = useCallback((nextSellerId: string | null) => {
    setScopeSellerId(nextSellerId);
    mutate({ sellerId: nextSellerId });
  }, [mutate, setScopeSellerId]);
  const toggleSort = useCallback((sort: Exclude<CustomerListSortKey, "attention">) => {
    setState((current) => updateCustomersListState(current, {
      sort,
      dir: current.sort === sort
        ? current.dir === "asc" ? "desc" : "asc"
        : sort === "nome" || sort === "city" || sort === "sellerName" ? "asc" : "desc",
    }));
  }, []);
  const setPage = useCallback((page: number) => mutate({ page }), [mutate]);
  const resetFilters = useCallback(() => {
    setScopeSellerId(null);
    setState(DEFAULT_STATE);
  }, [setScopeSellerId]);
  const listSearch = useMemo(
    () => buildCustomersListSearch({ ...state, sellerId }, sellerAccess),
    [sellerAccess, sellerId, state],
  );
  return {
    state: { ...state, sellerId },
    setSearch,
    setFilter,
    setSellerId,
    toggleSort,
    setPage,
    resetFilters,
    listSearch,
  };
}
