import { useCallback, useEffect, useMemo, useState } from "react";

import {
  collectDistinctClients,
  collectDistinctFiliais,
  computeSummaryFromItems,
  DEFAULT_FILTERS,
  filterPedidosItems,
  type OpenOrdersTotvsFilters,
} from "../utils/filterItems";
import type { StockFilter } from "../utils/statusBadges";
import { allocateStockToOrders } from "../utils/stockAllocation";
import { allocateOpsToOrders, buildOpsProductIndex } from "../utils/opAllocation";
import { useOpenOrdersTotvs } from "./useOpenOrdersTotvs";
import {
  DEFAULT_SORT,
  sortPedidosItems,
  type SortDirection,
  type SortKey,
} from "../utils/sortItems";

export const PAGE_SIZE = 50;

const STOCK_QUERY_VALUES = new Set<string>(["com_estoque", "parcial", "sem_estoque"]);

function readOrdersDeepLinkFilters(): Partial<OpenOrdersTotvsFilters> {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const patch: Partial<OpenOrdersTotvsFilters> = {};
  const stock = (params.get("stock") ?? "").trim();
  if (STOCK_QUERY_VALUES.has(stock)) patch.stockStatus = stock as StockFilter;
  const focus = (params.get("focus") ?? "").trim().toLowerCase();
  if (focus === "late" || focus === "atraso") patch.lateOnly = true;
  return patch;
}

function clearOrdersDeepLinkQueryFromUrl(): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  let changed = false;
  for (const key of ["stock", "focus"]) {
    if (url.searchParams.has(key)) {
      url.searchParams.delete(key);
      changed = true;
    }
  }
  if (!changed) return;
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

export function useOpenOrdersDashboard(sellerId?: string | null) {
  const { data, opsData, opsWarning, loading, error, reload } =
    useOpenOrdersTotvs(sellerId);
  const [filters, setFilters] = useState<OpenOrdersTotvsFilters>(() => ({
    ...DEFAULT_FILTERS,
    ...readOrdersDeepLinkFilters(),
  }));
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<SortKey>(DEFAULT_SORT.key);
  const [sortDirection, setSortDirection] = useState<SortDirection>(DEFAULT_SORT.direction);

  useEffect(() => {
    clearOrdersDeepLinkQueryFromUrl();
  }, []);

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
