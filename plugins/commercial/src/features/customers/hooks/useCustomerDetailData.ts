import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  enrichPortfolioCustomers,
  searchActiveCustomers,
} from "../../../api/commercialPortfolioApi";
import { getCustomerOpenOrdersTotvs } from "../../../api/openOrdersTotvsApi";
import type { OpenOrdersTotvsItem } from "../../../types/openOrdersTotvs";
import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import {
  aggregateCustomerOrders,
  selectAttentionOrders,
} from "../utils/customerOrderAggregation";
import { aggregateCustomers } from "../utils/customerAggregation";
import {
  buildIdentityCustomerSummary,
  mergeCustomerIdentity,
} from "../utils/customerIdentitySummary";

export type UseCustomerDetailDataResult = {
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  ordersError: string | null;
  identityError: string | null;
  hasData: boolean;
  lastSuccessAt: Date | null;
  reload: () => void;
  /** Cliente encontrado; null só se identidade falhar; undefined enquanto carrega. */
  customer: CustomerSummary | null | undefined;
  orders: CustomerOrderSummary[];
  attentionOrders: CustomerOrderSummary[];
  enrichmentLoading: boolean;
};

/**
 * Detalhe Conta: identidade (search + enrichment 1 par) + pedidos por cliente
 * (sem dump global `/open-orders/`).
 */
export function useCustomerDetailData(
  codigo: string,
  loja: string,
  options?: {
    sellerNameByKey?: ReadonlyMap<string, string>;
  },
): UseCustomerDetailDataResult {
  const sellerNameByKey = options?.sellerNameByKey;
  const [identity, setIdentity] = useState<CustomerSummary | null | undefined>(
    undefined,
  );
  const [identityError, setIdentityError] = useState<string | null>(null);
  const [orderItems, setOrderItems] = useState<OpenOrdersTotvsItem[]>([]);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [ordersReady, setOrdersReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastSuccessAt, setLastSuccessAt] = useState<Date | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const hasDataRef = useRef(false);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const code = codigo.trim();
    const store = loja.trim();
    if (!code || !store) {
      setIdentity(null);
      setOrderItems([]);
      setOrdersReady(true);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const isRefresh = hasDataRef.current;
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setIdentityError(null);
    setOrdersError(null);
    if (!isRefresh) {
      setIdentity(undefined);
      setOrdersReady(false);
    }

    void (async () => {
      try {
        const identityPromise = (async () => {
          const [searchResult, enrichResult] = await Promise.allSettled([
            searchActiveCustomers(code, {
              page: 1,
              pageSize: 20,
              signal: controller.signal,
            }),
            enrichPortfolioCustomers(
              [{ customer_code: code, customer_store: store }],
              controller.signal,
            ),
          ]);
          if (controller.signal.aborted) {
            throw new DOMException("Aborted", "AbortError");
          }

          const searchErrors: string[] = [];
          const search =
            searchResult.status === "fulfilled" ? searchResult.value : null;
          if (searchResult.status === "rejected") {
            searchErrors.push(
              searchResult.reason instanceof Error
                ? searchResult.reason.message
                : "Falha ao buscar cadastro.",
            );
          }

          const enrichItems =
            enrichResult.status === "fulfilled" ? enrichResult.value : [];
          if (enrichResult.status === "rejected") {
            searchErrors.push(
              enrichResult.reason instanceof Error
                ? enrichResult.reason.message
                : "Falha ao enriquecer cadastro.",
            );
          }

          // Só bloqueia se search e enrichment falharem juntos.
          if (!search && enrichResult.status === "rejected") {
            throw new Error(searchErrors.join(" ") || "Erro ao carregar identidade.");
          }
          // Enrichment falhou → aviso (FAT 12m etc.); search sozinho não derruba a Conta.
          setIdentityError(
            enrichResult.status === "rejected"
              ? searchErrors.join(" ") || "Não foi possível enriquecer o cadastro."
              : null,
          );

          const hit =
            search?.items.find(
              (item) =>
                item.code.trim() === code && item.store.trim() === store,
            ) ??
            search?.items.find((item) => item.code.trim() === code) ??
            null;
          const enrich =
            enrichItems.find(
              (item) =>
                item.customer_code.trim() === code &&
                item.customer_store.trim() === store,
            ) ?? null;
          const sellerName =
            sellerNameByKey?.get(`${code}|${store}`) ?? null;
          return buildIdentityCustomerSummary({
            codigo: code,
            loja: store,
            nome: hit?.name ?? null,
            enrichment: enrich,
            sellerName,
          });
        })();

        const ordersPromise = getCustomerOpenOrdersTotvs(code, store, controller.signal)
          .then((data) => data.items ?? [])
          .catch((err: unknown) => {
            if (controller.signal.aborted) throw err;
            const message =
              err instanceof Error
                ? err.message
                : "Não foi possível carregar os pedidos em aberto.";
            setOrdersError(message);
            return [] as OpenOrdersTotvsItem[];
          });

        const [shell, items] = await Promise.all([
          identityPromise.catch((err: unknown) => {
            if (controller.signal.aborted) throw err;
            setIdentityError(
              err instanceof Error ? err.message : "Erro ao carregar identidade.",
            );
            return buildIdentityCustomerSummary({
              codigo: code,
              loja: store,
              nome: null,
              enrichment: null,
              sellerName: sellerNameByKey?.get(`${code}|${store}`) ?? null,
            });
          }),
          ordersPromise,
        ]);

        if (controller.signal.aborted) return;
        setIdentity(shell);
        setOrderItems(items);
        setOrdersReady(true);
        hasDataRef.current = true;
        setLastSuccessAt(new Date());
      } catch (err) {
        if (controller.signal.aborted) return;
        setIdentityError(
          err instanceof Error ? err.message : "Erro ao carregar a conta.",
        );
        setIdentity(
          buildIdentityCustomerSummary({
            codigo: code,
            loja: store,
            nome: null,
            enrichment: null,
            sellerName: sellerNameByKey?.get(`${code}|${store}`) ?? null,
          }),
        );
        setOrdersReady(true);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    })();

    return () => controller.abort();
  }, [codigo, loja, sellerNameByKey, reloadKey]);

  const fromOrders = useMemo(() => {
    if (!ordersReady) return undefined;
    const aggregated = aggregateCustomers(orderItems);
    return (
      aggregated.customers.find(
        (customer) =>
          customer.codigo.trim() === codigo.trim() &&
          customer.loja.trim() === loja.trim(),
      ) ?? null
    );
  }, [orderItems, ordersReady, codigo, loja]);

  const customer = useMemo(() => {
    if (identity === undefined && fromOrders === undefined) return undefined;
    return mergeCustomerIdentity(fromOrders ?? null, identity ?? null);
  }, [fromOrders, identity]);

  const orders = useMemo(() => {
    if (!customer?.lines?.length) return [];
    return aggregateCustomerOrders(customer.lines);
  }, [customer]);

  const attentionOrders = useMemo(() => {
    if (!customer) return [];
    return selectAttentionOrders(orders, customer.proximaEntrega);
  }, [customer, orders]);

  return {
    loading,
    refreshing,
    error: identityError,
    ordersError,
    identityError,
    hasData: Boolean(customer) || Boolean(lastSuccessAt),
    lastSuccessAt,
    reload,
    customer,
    orders,
    attentionOrders,
    enrichmentLoading: loading && identity === undefined,
  };
}
