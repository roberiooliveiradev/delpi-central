import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { enrichPortfolioCustomers } from "../../../api/customerEnrichmentApi";
import { getPedidosVendaAbertos } from "../../../api/pedidosVendaAbertosApi";
import type { PedidosVendaAbertosItem } from "../../../types/pedidosVendaAbertos";
import type {
  CustomerAggregationResult,
  CustomerAttentionFilter,
  CustomerListSortDirection,
  CustomerListSortKey,
  CustomerSummary,
} from "../types/customerSummary";
import { aggregateCustomers } from "../utils/customerAggregation";
import { filterCustomers } from "../utils/customerFilters";
import {
  resolveCustomerNextAction,
  resolveCustomerStatus,
} from "../utils/customerListPresentation";
import {
  ATTENTION_LIST_LIMIT,
  sortCustomers,
  sortCustomersByAttention,
} from "../utils/customerSorting";

const PAGE_SIZE = 20;

export type UseCustomersDataResult = {
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  hasData: boolean;
  items: PedidosVendaAbertosItem[];
  aggregation: CustomerAggregationResult | null;
  filteredCustomers: CustomerSummary[];
  pagedCustomers: CustomerSummary[];
  page: number;
  totalPages: number;
  setPage: (page: number) => void;
  attentionCustomers: CustomerSummary[];
  search: string;
  setSearch: (value: string) => void;
  filter: CustomerAttentionFilter;
  setFilter: (value: CustomerAttentionFilter) => void;
  sortKey: CustomerListSortKey;
  sortDirection: CustomerListSortDirection;
  toggleSort: (key: Exclude<CustomerListSortKey, "attention">) => void;
  resetFilters: () => void;
  lastSuccessAt: Date | null;
  reload: () => void;
  portfolioMessage: string | null;
  portfolioEmpty: boolean;
};

export function useCustomersData(
  sellerId?: string | null,
  options?: {
    sellerNameByKey?: ReadonlyMap<string, string>;
  },
): UseCustomersDataResult {
  const sellerNameByKey = options?.sellerNameByKey;
  const [items, setItems] = useState<PedidosVendaAbertosItem[]>([]);
  const [enrichmentByKey, setEnrichmentByKey] = useState<
    Record<
      string,
      {
        city: string | null;
        state: string | null;
        lastPurchaseDate: string | null;
        billed12m: number;
        hasAvatar: boolean;
        billingTrend: "up" | "down" | "stable" | "insufficient" | null;
        billingTrendPct: number | null;
      }
    >
  >({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSuccessAt, setLastSuccessAt] = useState<Date | null>(null);
  const [portfolioMessage, setPortfolioMessage] = useState<string | null>(null);
  const [portfolioEmpty, setPortfolioEmpty] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<CustomerAttentionFilter>("all");
  const [sortKey, setSortKey] = useState<CustomerListSortKey>("attention");
  const [sortDirection, setSortDirection] = useState<CustomerListSortDirection>("asc");
  const [page, setPage] = useState(1);
  const hasDataRef = useRef(false);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const isRefresh = hasDataRef.current;

    async function run() {
      try {
        if (isRefresh) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }
        setError(null);

        const data = await getPedidosVendaAbertos(controller.signal, {
          sellerId: sellerId || null,
        });
        setItems(data.items);
        setPortfolioEmpty(Boolean(data.portfolio?.empty));
        setPortfolioMessage(data.portfolio?.message ?? null);
        hasDataRef.current = true;
        setLastSuccessAt(new Date());

        const aggregated = aggregateCustomers(data.items);
        const pairs = aggregated.customers.map((customer) => ({
          customer_code: customer.codigo,
          customer_store: customer.loja,
        }));
        if (pairs.length > 0) {
          try {
            const enriched = await enrichPortfolioCustomers(pairs, controller.signal);
            if (controller.signal.aborted) return;
            const map: typeof enrichmentByKey = {};
            for (const item of enriched) {
              map[`${item.customer_code}|${item.customer_store}`] = {
                city: item.city,
                state: item.state,
                lastPurchaseDate: item.last_purchase_date,
                billed12m: item.billed_12m,
                hasAvatar: item.has_avatar,
                billingTrend: item.billing_trend ?? null,
                billingTrendPct:
                  item.billing_trend_pct === undefined || item.billing_trend_pct === null
                    ? null
                    : Number(item.billing_trend_pct),
              };
            }
            setEnrichmentByKey(map);
          } catch {
            if (!controller.signal.aborted) {
              setEnrichmentByKey({});
            }
          }
        } else {
          setEnrichmentByKey({});
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar os clientes.";
        setError(message);
        if (!hasDataRef.current) {
          setItems([]);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [reloadKey, sellerId]);

  const aggregation = useMemo(() => {
    if (!lastSuccessAt) return null;
    const base = aggregateCustomers(items);
    return {
      ...base,
      customers: base.customers.map((customer) => {
        const enrich = enrichmentByKey[customer.key];
        const withStatus = {
          ...customer,
          city: enrich?.city ?? null,
          state: enrich?.state ?? null,
          lastPurchaseDate: enrich?.lastPurchaseDate ?? null,
          billed12m: enrich?.billed12m ?? 0,
          hasAvatar: enrich?.hasAvatar ?? false,
          billingTrend: enrich?.billingTrend ?? null,
          billingTrendPct: enrich?.billingTrendPct ?? null,
        };
        return {
          ...withStatus,
          sellerName: sellerNameByKey?.get(customer.key) ?? null,
          status: resolveCustomerStatus(withStatus),
          nextAction: resolveCustomerNextAction(withStatus),
        };
      }),
    };
  }, [items, lastSuccessAt, enrichmentByKey, sellerNameByKey]);

  const filteredCustomers = useMemo(() => {
    if (!aggregation) return [];
    const filtered = filterCustomers(aggregation.customers, search, filter);
    return sortCustomers(filtered, sortKey, sortDirection);
  }, [aggregation, search, filter, sortKey, sortDirection]);

  const totalPages = Math.max(1, Math.ceil(filteredCustomers.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pagedCustomers = useMemo(() => {
    const start = (safePage - 1) * PAGE_SIZE;
    return filteredCustomers.slice(start, start + PAGE_SIZE);
  }, [filteredCustomers, safePage]);

  useEffect(() => {
    setPage(1);
  }, [search, filter, sortKey, sortDirection, sellerId]);

  const attentionCustomers = useMemo(() => {
    if (!aggregation) return [];
    return sortCustomersByAttention(aggregation.customers)
      .filter((customer) => customer.temAtraso)
      .slice(0, ATTENTION_LIST_LIMIT);
  }, [aggregation]);

  const toggleSort = useCallback((key: Exclude<CustomerListSortKey, "attention">) => {
    setSortKey((current) => {
      if (current === key) {
        setSortDirection((dir) => (dir === "asc" ? "desc" : "asc"));
        return current;
      }
      setSortDirection(key === "nome" || key === "city" || key === "sellerName" ? "asc" : "desc");
      return key;
    });
  }, []);

  const resetFilters = useCallback(() => {
    setSearch("");
    setFilter("all");
    setSortKey("attention");
    setSortDirection("asc");
    setPage(1);
  }, []);

  return {
    loading,
    refreshing,
    error,
    hasData: Boolean(lastSuccessAt),
    items,
    aggregation,
    filteredCustomers,
    pagedCustomers,
    page: safePage,
    totalPages,
    setPage,
    attentionCustomers,
    search,
    setSearch,
    filter,
    setFilter,
    sortKey,
    sortDirection,
    toggleSort,
    resetFilters,
    lastSuccessAt,
    reload,
    portfolioMessage,
    portfolioEmpty,
  };
}
