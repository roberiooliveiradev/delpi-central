import { useCallback, useEffect, useMemo, useState } from "react";

import {
  collectDistinctClients,
  collectDistinctFiliais,
  computeSummaryFromItems,
  DEFAULT_FILTERS,
  filterPedidosItems,
  type OpenOrdersTotvsFilters,
} from "../utils/filterItems";
import {
  isOpenOrdersListPath,
  parseOpenOrdersListUrlState,
  syncOpenOrdersListStateToUrl,
  type OpenOrdersSellerAccess,
} from "../utils/openOrdersDeepLink";
import { allocateStockToOrders } from "../utils/stockAllocation";
import { allocateOpsToOrders, buildOpsProductIndex } from "../utils/opAllocation";
import { useOpenOrdersTotvs } from "./useOpenOrdersTotvs";
import {
  sortPedidosItems,
  type SortDirection,
  type SortKey,
} from "../utils/sortItems";

export const PAGE_SIZE = 50;

type OpenOrdersUrlOptions = {
  basePath?: string;
  sellerAccess?: OpenOrdersSellerAccess;
  sellerScopeLoading?: boolean;
  onSellerIdChange?: (sellerId: string | null) => void;
};

export function useOpenOrdersDashboard(
  sellerId?: string | null,
  urlOptions: OpenOrdersUrlOptions = {},
) {
  const {
    basePath,
    sellerAccess,
    sellerScopeLoading = false,
    onSellerIdChange,
  } = urlOptions;
  const initialUrlState = useMemo(
    () => parseOpenOrdersListUrlState(undefined, sellerAccess),
    [sellerAccess],
  );
  const { data, opsData, opsWarning, loading, error, reload } =
    useOpenOrdersTotvs(sellerId);
  const [filters, setFilters] = useState<OpenOrdersTotvsFilters>(initialUrlState.filters);
  const [page, setPage] = useState(initialUrlState.page);
  const [sortKey, setSortKey] = useState<SortKey>(initialUrlState.sortKey);
  const [sortDirection, setSortDirection] = useState<SortDirection>(
    initialUrlState.sortDirection,
  );
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    if (!loading && data) {
      setLastUpdatedAt(new Date());
    }
  }, [loading, data]);

  useEffect(() => {
    if (sellerScopeLoading) return;
    if (initialUrlState.sellerId !== sellerId) {
      onSellerIdChange?.(initialUrlState.sellerId);
    }
  }, [initialUrlState.sellerId, onSellerIdChange, sellerId, sellerScopeLoading]);

  useEffect(() => {
    const restoreFromUrl = () => {
      if (!isOpenOrdersListPath(window.location.pathname, basePath)) return;
      const state = parseOpenOrdersListUrlState(undefined, sellerAccess);
      setFilters(state.filters);
      setPage(state.page);
      setSortKey(state.sortKey);
      setSortDirection(state.sortDirection);
      onSellerIdChange?.(state.sellerId);
    };
    window.addEventListener("popstate", restoreFromUrl);
    return () => window.removeEventListener("popstate", restoreFromUrl);
  }, [basePath, onSellerIdChange, sellerAccess]);

  const allItems = useMemo(() => data?.items ?? [], [data?.items]);

  const opsIndex = useMemo(() => buildOpsProductIndex(opsData), [opsData]);

  const allocatedItems = useMemo(
    () => allocateStockToOrders(allItems),
    [allItems],
  );

  const itemsWithOpForecast = useMemo(
    () => allocateOpsToOrders(allocatedItems, opsIndex),
    [allocatedItems, opsIndex],
  );

  const filiais = useMemo(() => collectDistinctFiliais(itemsWithOpForecast), [itemsWithOpForecast]);
  const clients = useMemo(() => collectDistinctClients(itemsWithOpForecast), [itemsWithOpForecast]);

  const attentionBaseItems = useMemo(
    () =>
      filterPedidosItems(itemsWithOpForecast, {
        ...filters,
        stockStatus: "",
        lateOnly: false,
      }),
    [itemsWithOpForecast, filters],
  );

  const attentionSummary = useMemo(
    () => computeSummaryFromItems(attentionBaseItems),
    [attentionBaseItems],
  );

  const filteredItems = useMemo(
    () => filterPedidosItems(itemsWithOpForecast, filters),
    [itemsWithOpForecast, filters],
  );

  const sortedItems = useMemo(
    () => sortPedidosItems(filteredItems, sortKey, sortDirection),
    [filteredItems, sortKey, sortDirection],
  );

  const summary = useMemo(() => computeSummaryFromItems(filteredItems), [filteredItems]);

  const totalPages = Math.max(1, Math.ceil(sortedItems.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);

  useEffect(() => {
    if (loading || sellerScopeLoading) return;
    syncOpenOrdersListStateToUrl(
      {
        filters,
        sellerId: sellerId ?? null,
        sortKey,
        sortDirection,
        page: currentPage,
      },
      basePath,
    );
  }, [
    basePath,
    currentPage,
    filters,
    loading,
    sellerId,
    sellerScopeLoading,
    sortDirection,
    sortKey,
  ]);

  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return sortedItems.slice(start, start + PAGE_SIZE);
  }, [sortedItems, currentPage]);

  const updateFilters = useCallback((patch: Partial<OpenOrdersTotvsFilters>) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
  }, []);

  const toggleSort = useCallback((key: SortKey) => {
    setSortKey((currentKey) => {
      if (currentKey === key) {
        setSortDirection((currentDirection) =>
          currentDirection === "asc" ? "desc" : "asc",
        );
        return currentKey;
      }
      setSortDirection("asc");
      return key;
    });
    setPage(1);
  }, []);

  const hasActiveFilters =
    Boolean(filters.search.trim()) ||
    Boolean(filters.filial) ||
    filters.clientCodes.length > 0 ||
    Boolean(filters.stockStatus) ||
    Boolean(filters.dateStart) ||
    Boolean(filters.dateEnd) ||
    filters.lateOnly;

  return {
    loading,
    error,
    opsWarning,
    reload,
    lastUpdatedAt,
    portfolioEmpty: Boolean(data?.portfolio?.empty),
    portfolioMessage: data?.portfolio?.message ?? null,
    allItemsCount: allItems.length,
    filteredItems,
    paginatedItems,
    summary,
    attentionSummary,
    filters,
    updateFilters,
    resetFilters,
    hasActiveFilters,
    filiais,
    clients,
    page: currentPage,
    pageSize: PAGE_SIZE,
    totalPages,
    totalFiltered: sortedItems.length,
    sortedItems,
    setPage,
    sortKey,
    sortDirection,
    toggleSort,
  };
}
