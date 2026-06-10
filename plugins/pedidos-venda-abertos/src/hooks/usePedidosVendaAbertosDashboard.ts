import { useCallback, useMemo, useState } from "react";

import type { PedidosVendaAbertosItem } from "../types/pedidosVendaAbertos";
import {
  collectDistinctClients,
  collectDistinctFiliais,
  computeSummaryFromItems,
  DEFAULT_FILTERS,
  filterPedidosItems,
  type PedidosVendaAbertosFilters,
} from "../utils/filterItems";
import { allocateStockToOrders } from "../utils/stockAllocation";
import { allocateOpsToOrders, buildOpsProductIndex } from "../utils/opAllocation";
import { usePedidosVendaAbertos } from "./usePedidosVendaAbertos";
import {
  DEFAULT_SORT,
  sortPedidosItems,
  type SortDirection,
  type SortKey,
} from "../utils/sortItems";

export const PAGE_SIZE = 50;

export function usePedidosVendaAbertosDashboard() {
  const { data, opsData, opsWarning, loading, error, reload } = usePedidosVendaAbertos();
  const [filters, setFilters] = useState<PedidosVendaAbertosFilters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<SortKey>(DEFAULT_SORT.key);
  const [sortDirection, setSortDirection] = useState<SortDirection>(DEFAULT_SORT.direction);

  const allItems = useMemo(() => data?.items ?? [], [data?.items]);

  const opsIndex = useMemo(() => buildOpsProductIndex(opsData), [opsData]);

  const allocatedItems = useMemo(
    () => allocateStockToOrders(allItems),
    [allItems],
  );

  const itemsWithOpPrevisao = useMemo(
    () => allocateOpsToOrders(allocatedItems, opsIndex),
    [allocatedItems, opsIndex],
  );

  const filiais = useMemo(() => collectDistinctFiliais(itemsWithOpPrevisao), [itemsWithOpPrevisao]);
  const clients = useMemo(() => collectDistinctClients(itemsWithOpPrevisao), [itemsWithOpPrevisao]);

  const filteredItems = useMemo(
    () => filterPedidosItems(itemsWithOpPrevisao, filters),
    [itemsWithOpPrevisao, filters],
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

  const updateFilters = useCallback((patch: Partial<PedidosVendaAbertosFilters>) => {
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
    Boolean(filters.dateEnd);

  return {
    loading,
    error,
    opsWarning,
    reload,
    allItemsCount: allItems.length,
    filteredItems,
    paginatedItems,
    summary,
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

export type UsePedidosVendaAbertosDashboardResult = ReturnType<
  typeof usePedidosVendaAbertosDashboard
>;

export type { PedidosVendaAbertosItem };
