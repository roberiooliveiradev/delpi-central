import { useMemo } from "react";

import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import { useCustomersData, type UseCustomersDataResult } from "./useCustomersData";
import {
  aggregateCustomerOrders,
  selectAttentionOrders,
} from "../utils/customerOrderAggregation";
import { findCustomerByIdentity } from "../utils/customerLookup";

export type UseCustomerDetailDataResult = {
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  hasData: boolean;
  lastSuccessAt: Date | null;
  reload: () => void;
  /** Cliente encontrado; null após carga sem match; undefined enquanto agregação indisponível. */
  customer: CustomerSummary | null | undefined;
  orders: CustomerOrderSummary[];
  attentionOrders: CustomerOrderSummary[];
  /** Dados brutos do hook compartilhado (filtros da lista não afetam o detalhe). */
  listData: UseCustomersDataResult;
};

/**
 * Detalhe do cliente: reutiliza getOpenOrdersTotvs via useCustomersData.
 * Deep link independente da visita prévia à lista.
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

  const customer = useMemo(() => {
    if (!listData.aggregation) return undefined;
    return findCustomerByIdentity(listData.aggregation.customers, codigo, loja);
  }, [listData.aggregation, codigo, loja]);

  const orders = useMemo(() => {
    if (!customer) return [];
    return aggregateCustomerOrders(customer.lines);
  }, [customer]);

  const attentionOrders = useMemo(() => {
    if (!customer) return [];
    return selectAttentionOrders(orders, customer.proximaEntrega);
  }, [customer, orders]);

  return {
    loading: listData.loading,
    refreshing: listData.refreshing,
    error: listData.error,
    hasData: listData.hasData,
    lastSuccessAt: listData.lastSuccessAt,
    reload: listData.reload,
    customer,
    orders,
    attentionOrders,
    listData,
  };
}
