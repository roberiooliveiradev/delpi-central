import { useCallback, useEffect, useState } from "react";

import { fetchProductionOrdersReport } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { PpcBranch, ProductionOrdersReportPayload } from "../types";

export type ProductionOrderTriFilter = "yes" | "no" | "all";

export type ProductionOrdersFilters = {
  opKey: string;
  productCode: string;
  motherOnly: ProductionOrderTriFilter;
  openOnly: ProductionOrderTriFilter;
  deliveryStart: string;
  deliveryEnd: string;
  actualEndStart: string;
  actualEndEnd: string;
  page: number;
  pageSize: number;
  sort: string;
};

export const PRODUCTION_ORDERS_DEFAULT_FILTERS: ProductionOrdersFilters = {
  opKey: "",
  productCode: "",
  motherOnly: "all",
  openOnly: "yes",
  deliveryStart: "",
  deliveryEnd: "",
  actualEndStart: "",
  actualEndEnd: "",
  page: 1,
  pageSize: 50,
  sort: "op_asc",
};

export function isClosedProductionOrdersFilter(openOnly: ProductionOrderTriFilter): boolean {
  return openOnly === "no";
}

export function useProductionOrdersReport(branch: PpcBranch, filters: ProductionOrdersFilters) {
  const [data, setData] = useState<ProductionOrdersReportPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchProductionOrdersReport({
      branch,
      opKey: filters.opKey,
      productCode: filters.productCode,
      motherOnly: filters.motherOnly,
      openOnly: filters.openOnly,
      deliveryStart: filters.deliveryStart || null,
      deliveryEnd: filters.deliveryEnd || null,
      actualEndStart: isClosedProductionOrdersFilter(filters.openOnly)
        ? filters.actualEndStart || null
        : null,
      actualEndEnd: isClosedProductionOrdersFilter(filters.openOnly)
        ? filters.actualEndEnd || null
        : null,
      sort: filters.sort,
      page: filters.page,
      pageSize: filters.pageSize,
      signal: controller.signal,
    })
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.reports.loadError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    branch,
    filters.actualEndEnd,
    filters.actualEndStart,
    filters.deliveryEnd,
    filters.deliveryStart,
    filters.motherOnly,
    filters.opKey,
    filters.openOnly,
    filters.page,
    filters.pageSize,
    filters.productCode,
    filters.sort,
    reloadToken,
  ]);

  return {
    data,
    loading: loading && data === null,
    refreshing: loading && data !== null,
    error,
    reload,
  };
}
