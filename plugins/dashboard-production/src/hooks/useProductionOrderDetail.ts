import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getProductStructure, getProductSummary } from "../api/productApi";
import { getProductionOrderByOp } from "../api/productionApi";
import type {
  IntermediateProductionOrderRow,
  ProductionOrderByOpData,
  ProductionOrderProductType,
  ProductStructureData,
  ProductSummaryData,
} from "../types/production";
import {
  mapLinkedOrdersToIntermediateRows,
  summarizeIntermediateOtd,
} from "../utils/intermediateProductionOrders";
import { formatProductionApiError } from "../utils/formatProductionApiError";

export type ProductionOrderDetailOptions = {
  branch?: string;
  productType?: ProductionOrderProductType;
  linkedSortBy?: string | null;
  linkedSortDir?: "asc" | "desc";
};

export type ProductionOrderDetailState = {
  orderData: ProductionOrderByOpData | null;
  productData: ProductSummaryData | null;
  structureData: ProductStructureData | null;
  intermediateOrders: IntermediateProductionOrderRow[];
  intermediateSummary: ReturnType<typeof summarizeIntermediateOtd>;
  loading: boolean;
  linkedOrdersRefreshing: boolean;
  error: string | null;
  reload: () => void;
};

export function useProductionOrderDetail(
  productionOrder: string,
  options: ProductionOrderDetailOptions = {}
): ProductionOrderDetailState {
  const { branch, productType, linkedSortBy, linkedSortDir = "asc" } = options;

  const [orderData, setOrderData] = useState<ProductionOrderByOpData | null>(
    null
  );
  const [productData, setProductData] = useState<ProductSummaryData | null>(
    null
  );
  const [structureData, setStructureData] = useState<ProductStructureData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [linkedOrdersRefreshing, setLinkedOrdersRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const loadedProductKeyRef = useRef("");

  const reload = useCallback(() => {
    loadedProductKeyRef.current = "";
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const normalizedOrder = productionOrder.trim();
    if (!normalizedOrder) {
      setOrderData(null);
      setProductData(null);
      setStructureData(null);
      setLoading(false);
      setError("Ordem de produção inválida.");
      return;
    }

    const controller = new AbortController();
    const productKey = `${normalizedOrder}-${branch ?? ""}-${productType ?? ""}`;
    const hasCachedProduct = loadedProductKeyRef.current === productKey;

    async function run() {
      if (hasCachedProduct) {
        setLinkedOrdersRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      if (!hasCachedProduct) {
        setOrderData(null);
        setProductData(null);
        setStructureData(null);
      }

      try {
        const orderResult = await getProductionOrderByOp(
          normalizedOrder,
          {
            branch,
            productType,
            linkedSortBy: linkedSortBy ?? undefined,
            linkedSortDir,
          },
          controller.signal
        );

        const productCode = orderResult.order.product_code?.trim();
        if (!productCode) {
          throw new Error("Produto da OP não encontrado.");
        }

        setOrderData(orderResult);

        if (!hasCachedProduct) {
          const [summaryResult, structureResult] = await Promise.all([
            getProductSummary(productCode, controller.signal),
            getProductStructure(productCode, controller.signal),
          ]);

          setProductData(summaryResult);
          setStructureData(structureResult);
          loadedProductKeyRef.current = productKey;
        }
      } catch (reason) {
        if (controller.signal.aborted) return;
        setError(formatProductionApiError(reason));
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setLinkedOrdersRefreshing(false);
        }
      }
    }

    void run();

    return () => controller.abort();
  }, [
    productionOrder,
    branch,
    productType,
    linkedSortBy,
    linkedSortDir,
    reloadKey,
  ]);

  const intermediateOrders = useMemo(
    () =>
      mapLinkedOrdersToIntermediateRows(
        orderData?.linked_orders ?? [],
        structureData
      ),
    [orderData?.linked_orders, structureData]
  );

  const intermediateSummary = useMemo(() => {
    if (orderData?.link_summary) {
      return {
        total: orderData.link_summary.total_pi_orders,
        on_time: orderData.link_summary.on_time_ops,
        late: orderData.link_summary.late_ops,
        open: orderData.link_summary.open_ops,
      };
    }

    return summarizeIntermediateOtd(intermediateOrders);
  }, [orderData?.link_summary, intermediateOrders]);

  return {
    orderData,
    productData,
    structureData,
    intermediateOrders,
    intermediateSummary,
    loading,
    linkedOrdersRefreshing,
    error,
    reload,
  };
}
