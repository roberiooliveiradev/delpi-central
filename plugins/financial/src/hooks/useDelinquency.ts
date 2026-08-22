import { useMemo } from "react";

import { fetchDelinquencyDashboard, fetchDelinquencyTitles } from "../api/financialApi";
import { copy } from "../content/copy";
import type {
  DelinquencyAgingBucket,
  DelinquencyCustomer,
  DelinquencyCustomersPayload,
  DelinquencyMonthPoint,
  DelinquencySummary,
  DelinquencyTitlesPayload,
} from "../types";
import { useAsyncResource } from "./useAsyncResource";

export type DelinquencyFilters = {
  startDate: string | null;
  endDate: string | null;
  clientCode: string | null;
  clientStore: string | null;
  onlyWithDelays: boolean;
  page: number;
  sortBy: string;
  sortDir: "asc" | "desc";
};

export type DelinquencyBundle = {
  summary: DelinquencySummary;
  monthly: DelinquencyMonthPoint[];
  aging: DelinquencyAgingBucket[];
  customers: DelinquencyCustomersPayload;
  topDelinquentCustomers: DelinquencyCustomer[];
};

export function useDelinquency(filters: DelinquencyFilters) {
  const key = useMemo(
    () =>
      [
        filters.startDate,
        filters.endDate,
        filters.clientCode,
        filters.clientStore,
        filters.onlyWithDelays,
        filters.page,
        filters.sortBy,
        filters.sortDir,
      ].join("|"),
    [
      filters.startDate,
      filters.endDate,
      filters.clientCode,
      filters.clientStore,
      filters.onlyWithDelays,
      filters.page,
      filters.sortBy,
      filters.sortDir,
    ],
  );

  return useAsyncResource<DelinquencyBundle>(
    async (signal) => {
      const payload = await fetchDelinquencyDashboard({
        startDate: filters.startDate,
        endDate: filters.endDate,
        customerCode: filters.clientCode,
        store: filters.clientStore,
        onlyWithDelays: filters.onlyWithDelays,
        page: filters.page,
        sortBy: filters.sortBy,
        sortDir: filters.sortDir,
        signal,
      });
      return {
        summary: payload.summary,
        monthly: payload.monthly.items,
        aging: payload.aging.items,
        customers: payload.customers,
        topDelinquentCustomers: payload.topDelinquentCustomers.items,
      };
    },
    [key],
    copy.delinquency.loadError,
  );
}

export function useDelinquencyTitles(params: {
  customerCode: string | null;
  store: string | null;
  status: string | null;
  delayRange: string | null;
  startDate: string | null;
  endDate: string | null;
  page: number;
  enabled: boolean;
}) {
  const key = [
    params.enabled,
    params.customerCode,
    params.store,
    params.status,
    params.delayRange,
    params.startDate,
    params.endDate,
    params.page,
  ].join("|");

  return useAsyncResource<DelinquencyTitlesPayload | null>(
    (signal) => {
      if (!params.enabled || !params.customerCode) {
        return Promise.resolve(null);
      }
      return fetchDelinquencyTitles({
        customerCode: params.customerCode,
        store: params.store,
        status: params.status,
        delayRange: params.delayRange,
        startDate: params.startDate,
        endDate: params.endDate,
        page: params.page,
        signal,
      });
    },
    [key],
    copy.delinquency.loadError,
  );
}
