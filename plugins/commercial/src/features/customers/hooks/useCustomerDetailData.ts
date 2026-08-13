import { useEffect, useMemo, useState } from "react";

import {
  enrichPortfolioCustomers,
  searchActiveCustomers,
} from "../../../api/commercialPortfolioApi";
import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import { useCustomersData, type UseCustomersDataResult } from "./useCustomersData";
import {
  aggregateCustomerOrders,
  selectAttentionOrders,
} from "../utils/customerOrderAggregation";
import { findCustomerByIdentity } from "../utils/customerLookup";
import {
  buildIdentityCustomerSummary,
  mergeCustomerIdentity,
} from "../utils/customerIdentitySummary";

export type UseCustomerDetailDataResult = {
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  hasData: boolean;
  lastSuccessAt: Date | null;
  reload: () => void;
  /** Cliente encontrado; null só se identidade falhar; undefined enquanto carrega. */
  customer: CustomerSummary | null | undefined;
  orders: CustomerOrderSummary[];
  attentionOrders: CustomerOrderSummary[];
  listData: UseCustomersDataResult;
};

/**
 * Detalhe Conta: identidade por par (search + enrichment) + pedidos via open-orders.
 */
export function useCustomerDetailData(
  codigo: string,
  loja: string,
  options?: {
    sellerNameByKey?: ReadonlyMap<string, string>;
    sellerId?: string | null;
  },
): UseCustomerDetailDataResult {
  const sellerNameByKey = options?.sellerNameByKey;
  const listData = useCustomersData(options?.sellerId ?? null, { sellerNameByKey });
  const [identity, setIdentity] = useState<CustomerSummary | null | undefined>(
    undefined,
  );
  const [identityError, setIdentityError] = useState<string | null>(null);
  const [identityTick, setIdentityTick] = useState(0);

  useEffect(() => {
    const code = codigo.trim();
    const store = loja.trim();
    if (!code || !store) {
      setIdentity(null);
      return;
    }
    const controller = new AbortController();
    setIdentity(undefined);
    setIdentityError(null);
    void (async () => {
      try {
        const [search, enrichItems] = await Promise.all([
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
        if (controller.signal.aborted) return;
        const hit =
          search.items.find(
            (item) =>
              item.code.trim() === code && item.store.trim() === store,
          ) ??
          search.items.find((item) => item.code.trim() === code) ??
          null;
        const enrich =
          enrichItems.find(
            (item) =>
              item.customer_code.trim() === code &&
              item.customer_store.trim() === store,
          ) ?? null;
        const sellerName =
          sellerNameByKey?.get(`${code}|${store}`) ?? null;
        const shell = buildIdentityCustomerSummary({
          codigo: code,
          loja: store,
          nome: hit?.name ?? null,
          enrichment: enrich,
          sellerName,
        });
        setIdentity(shell);
      } catch (err) {
        if (controller.signal.aborted) return;
        setIdentityError(
          err instanceof Error ? err.message : "Erro ao carregar identidade.",
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
      }
    })();
    return () => controller.abort();
  }, [codigo, loja, sellerNameByKey, identityTick]);

  const fromOrders = useMemo(() => {
    if (!listData.aggregation) return undefined;
    return findCustomerByIdentity(listData.aggregation.customers, codigo, loja);
  }, [listData.aggregation, codigo, loja]);

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

  const reload = () => {
    listData.reload();
    setIdentityTick((n) => n + 1);
  };

  const loading =
    (identity === undefined && !identityError) ||
    (listData.loading && customer === undefined);
  const hasData = Boolean(customer) || listData.hasData;

  return {
    loading,
    refreshing: listData.refreshing,
    error: identityError || listData.error,
    hasData,
    lastSuccessAt: listData.lastSuccessAt,
    reload,
    customer,
    orders,
    attentionOrders,
    listData,
  };
}
