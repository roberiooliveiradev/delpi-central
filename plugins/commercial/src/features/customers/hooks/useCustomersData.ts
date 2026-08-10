import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { enrichPortfolioCustomersBatched } from "../../../api/customerEnrichmentApi";
import { getOpenOrdersTotvs } from "../../../api/openOrdersTotvsApi";
import type { OpenOrdersTotvsItem } from "../../../types/openOrdersTotvs";
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
import type { CustomersListState } from "./useCustomersListState";

const PAGE_SIZE = 20;

export type UseCustomersDataResult = {
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  hasData: boolean;
  items: OpenOrdersTotvsItem[];
  aggregation: CustomerAggregationResult | null;
  filteredCustomers: CustomerSummary[];
  pagedCustomers: CustomerSummary[];
  page: number;
  totalPages: number;
  attentionCustomers: CustomerSummary[];
  lastSuccessAt: Date | null;
  reload: () => void;
  portfolioMessage: string | null;
  portfolioEmpty: boolean;
  enrichment: {
    loading: boolean;
    error: string | null;
    covered: number;
    total: number;
    failedBatches: number;
    lastSuccessAt: Date | null;
  };
};

export function useCustomersData(
  sellerId?: string | null,
  options?: {
    sellerNameByKey?: ReadonlyMap<string, string>;
    listState?: CustomersListState;
  },
): UseCustomersDataResult {
  const sellerNameByKey = options?.sellerNameByKey;
  const [items, setItems] = useState<OpenOrdersTotvsItem[]>([]);
  const [enrichmentByKey, setEnrichmentByKey] = useState<
    Record<
      string,
      {
        city: string | null;
        state: string | null;
        lastPurchaseDate: string | null;
        billed12m: number | null;
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
  const [enrichmentLoading, setEnrichmentLoading] = useState(false);
  const [enrichmentError, setEnrichmentError] = useState<string | null>(null);
  const [enrichmentCovered, setEnrichmentCovered] = useState(0);
  const [enrichmentTotal, setEnrichmentTotal] = useState(0);
  const [enrichmentFailedBatches, setEnrichmentFailedBatches] = useState(0);
  const [enrichmentLastSuccessAt, setEnrichmentLastSuccessAt] = useState<Date | null>(null);
  const [enrichmentKnownKeys, setEnrichmentKnownKeys] = useState<Set<string>>(() => new Set());
  const [reloadKey, setReloadKey] = useState(0);
  const hasDataRef = useRef(false);
  const listState = options?.listState;
  const search = listState?.q ?? "";
  const filter: CustomerAttentionFilter = listState?.focus ?? "all";
  const sortKey: CustomerListSortKey = listState?.sort ?? "attention";
  const sortDirection: CustomerListSortDirection = listState?.dir ?? "asc";
  const page = listState?.page ?? 1;

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

        const data = await getOpenOrdersTotvs(controller.signal, {
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
        setEnrichmentTotal(pairs.length);
        if (pairs.length > 0) {
          try {
            setEnrichmentLoading(true);
            setEnrichmentError(null);
            const enriched = await enrichPortfolioCustomersBatched(pairs, controller.signal);
            if (controller.signal.aborted) return;
            const map: typeof enrichmentByKey = {};
            const knownKeys = new Set<string>();
            for (const item of enriched.items) {
              const key = `${item.customer_code}|${item.customer_store}`;
              knownKeys.add(key);
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
            setEnrichmentByKey((current) => ({ ...current, ...map }));
            setEnrichmentKnownKeys(knownKeys);
            setEnrichmentCovered(enriched.coverage.covered);
            setEnrichmentFailedBatches(enriched.coverage.failedBatches);
            setEnrichmentError(enriched.partialError);
            if (enriched.coverage.covered > 0) setEnrichmentLastSuccessAt(new Date());
          } catch (err) {
            if (!controller.signal.aborted) {
              setEnrichmentError(
                err instanceof Error ? err.message : "Não foi possível enriquecer os clientes.",
              );
            }
          } finally {
            if (!controller.signal.aborted) setEnrichmentLoading(false);
          }
        } else {
          setEnrichmentByKey({});
          setEnrichmentCovered(0);
          setEnrichmentFailedBatches(0);
          setEnrichmentKnownKeys(new Set());
          setEnrichmentLoading(false);
          setEnrichmentError(null);
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
          billed12m: enrich?.billed12m ?? null,
          hasAvatar: enrich?.hasAvatar ?? false,
          billingTrend: enrich?.billingTrend ?? null,
          billingTrendPct: enrich?.billingTrendPct ?? null,
          coverageKnown: enrichmentKnownKeys.has(customer.key),
          enrichmentAvailable: Boolean(enrich),
        };
        return {
          ...withStatus,
          sellerName: sellerNameByKey?.get(customer.key) ?? null,
          status: resolveCustomerStatus(withStatus),
          nextAction: resolveCustomerNextAction(withStatus),
        };
      }),
    };
  }, [items, lastSuccessAt, enrichmentByKey, enrichmentKnownKeys, sellerNameByKey]);

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

  const attentionCustomers = useMemo(() => {
    if (!aggregation) return [];
    return sortCustomersByAttention(aggregation.customers)
      .filter((customer) => customer.temAtraso)
      .slice(0, ATTENTION_LIST_LIMIT);
  }, [aggregation]);

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
    attentionCustomers,
    lastSuccessAt,
    reload,
    portfolioMessage,
    portfolioEmpty,
    enrichment: {
      loading: enrichmentLoading,
      error: enrichmentError,
      covered: enrichmentCovered,
      total: enrichmentTotal,
      failedBatches: enrichmentFailedBatches,
      lastSuccessAt: enrichmentLastSuccessAt,
    },
  };
}
