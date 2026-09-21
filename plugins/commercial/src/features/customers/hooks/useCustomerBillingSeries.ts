import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCustomerBillingSeries,
} from "../../../api/customerBillingSeriesApi";
import {
  compareYearOffsets,
  type CompareYearsCount,
  clampCompareYears,
} from "../../analytics/utils/compareYears";
import { shiftPeriodRangeByYears } from "../../analytics/utils/periodShift";
import type { PortfolioBillingMetric } from "../../../content/billingMetric";
import { apiBillingMetric } from "../../../content/billingMetric";
import type { CustomerSummary } from "../types/customerSummary";
import {
  mergeBillingSeriesOverlays,
  type BillingSeriesOverlayPoint,
} from "../utils/mergeBillingSeriesOverlays";

export type BillingSeriesCustomerOption = {
  key: string;
  codigo: string;
  loja: string;
  nome: string;
};

export type BillingSeriesChartPoint = BillingSeriesOverlayPoint;

export type UseCustomerBillingSeriesResult = {
  /** Chaves selecionadas; vazio = toda a carteira. */
  selectedKeys: string[];
  setSelectedKeys: (keys: string[]) => void;
  customerOptions: BillingSeriesCustomerOption[];
  points: BillingSeriesChartPoint[];
  loading: boolean;
  error: string | null;
  totalValue: number;
  totalQuantity: number;
  quantityUnit: string | null;
  quantityMixedUnits: boolean;
  coverage: { covered: number; total: number; failedBatches: number };
  reload: () => void;
};

function buildRequestPairs(
  customers: CustomerSummary[] | undefined,
  selectedKeys: string[],
): Array<{ customer_code: string; customer_store: string; customer_center?: string }> {
  if (!customers?.length) return [];
  const mapRow = (customer: CustomerSummary) => {
    const center = customer.customerCenter?.trim();
    return {
      customer_code: customer.codigo,
      customer_store: customer.loja,
      ...(center ? { customer_center: center } : {}),
    };
  };
  if (!selectedKeys.length) return customers.map(mapRow);
  const selected = new Set(selectedKeys);
  return customers.filter((customer) => selected.has(customer.key)).map(mapRow);
}

function requestFingerprint(
  pairs: Array<{ customer_code: string; customer_store: string; customer_center?: string }>,
): string {
  return pairs
    .map((pair) => `${pair.customer_code}\0${pair.customer_store}\0${pair.customer_center ?? ""}`)
    .sort()
    .join("|");
}

export type UseCustomerBillingSeriesOptions = {
  enabled?: boolean;
  startDate?: string;
  endDate?: string;
  granularity?: "day" | "week" | "month" | "year";
  /** Overlay YoY legado (equivale a compareYears=1). */
  comparePriorYear?: boolean;
  /** Overlays −1a…−3a (0–3). Preferir sobre comparePriorYear. */
  compareYears?: CompareYearsCount;
  nature?: "gross" | "net";
  metric?: PortfolioBillingMetric;
  productCodes?: string[];
  productGroups?: string[];
  market?: "domestic" | "export";
  /** Controle externo do filtro de clientes (workspace Faturamento). */
  selectedKeys?: string[];
  onSelectedKeysChange?: (keys: string[]) => void;
};

export function useCustomerBillingSeries(
  customers: CustomerSummary[] | undefined,
  options?: UseCustomerBillingSeriesOptions,
): UseCustomerBillingSeriesResult {
  const enabled = options?.enabled ?? true;
  const startDate = options?.startDate;
  const endDate = options?.endDate;
  const granularity = options?.granularity;
  const compareYears = clampCompareYears(
    options?.compareYears ?? (options?.comparePriorYear ? 1 : 0),
  );
  const nature = options?.nature;
  const metric = options?.metric;
  const productCodesKey = (options?.productCodes ?? []).join("\0");
  const productGroupsKey = (options?.productGroups ?? []).join("\0");
  const market = options?.market;
  const productCodes = options?.productCodes;
  const productGroups = options?.productGroups;
  const controlledKeys = options?.selectedKeys;
  const onSelectedKeysChange = options?.onSelectedKeysChange;
  const [internalSelectedKeys, setInternalSelectedKeys] = useState<string[]>([]);
  const selectedKeys = controlledKeys ?? internalSelectedKeys;
  const setSelectedKeys = onSelectedKeysChange ?? setInternalSelectedKeys;
  const [points, setPoints] = useState<BillingSeriesChartPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coverage, setCoverage] = useState({ covered: 0, total: 0, failedBatches: 0 });
  const [quantityUnit, setQuantityUnit] = useState<string | null>(null);
  const [quantityMixedUnits, setQuantityMixedUnits] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const reload = useCallback(() => setReloadKey((value) => value + 1), []);

  const customerOptions = useMemo(() => {
    return (customers ?? [])
      .map((customer) => ({
        key: customer.key,
        codigo: customer.codigo,
        loja: customer.loja,
        nome: customer.nome,
      }))
      .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  }, [customers]);

  const optionKeySet = useMemo(
    () => new Set(customerOptions.map((customer) => customer.key)),
    [customerOptions],
  );
  const effectiveSelectedKeys = useMemo(
    () => selectedKeys.filter((key) => optionKeySet.has(key)),
    [optionKeySet, selectedKeys],
  );

  const requestPairs = useMemo(
    () => buildRequestPairs(customers, effectiveSelectedKeys),
    [customers, effectiveSelectedKeys],
  );
  const fingerprint = useMemo(() => requestFingerprint(requestPairs), [requestPairs]);

  useEffect(() => {
    if (!enabled || !fingerprint) return;

    const rows = fingerprint.split("|").map((token) => {
      const [customer_code, customer_store, customer_center = ""] = token.split("\0");
      return { customer_code, customer_store, customer_center };
    });
    const pairKeys = new Set<string>();
    const pairs: Array<{ customer_code: string; customer_store: string }> = [];
    for (const row of rows) {
      const key = `${row.customer_code}|${row.customer_store}`;
      if (pairKeys.has(key)) continue;
      pairKeys.add(key);
      pairs.push({ customer_code: row.customer_code, customer_store: row.customer_store });
    }
    const customerCenters = rows.some((row) => !row.customer_center)
      ? undefined
      : [...new Set(rows.map((row) => row.customer_center))].sort();

    const controller = new AbortController();
    let cancelled = false;
    setLoading(true);
    setError(null);

    const apiMetric = apiBillingMetric(metric ?? "value");
    const includeQuantityOverlay = metric === "both";

    const currentQuery = {
      months: startDate && endDate ? undefined : 12,
      startDate,
      endDate,
      granularity,
      nature,
      metric: apiMetric,
      productCodes,
      productGroups,
      market,
      customerCenters,
      signal: controller.signal,
    } as const;

    const offsets = compareYearOffsets(compareYears);
    const fetchMetric = (
      seriesMetric: "value" | "quantity",
      range?: { startDate: string; endDate: string },
    ) =>
      fetchCustomerBillingSeries(pairs, {
        months: range || (startDate && endDate) ? undefined : currentQuery.months,
        startDate: range?.startDate ?? startDate,
        endDate: range?.endDate ?? endDate,
        granularity,
        nature,
        metric: seriesMetric,
        productCodes,
        productGroups,
        market,
        customerCenters,
        signal: controller.signal,
      });

    const currentPromise = fetchCustomerBillingSeries(pairs, currentQuery);
    const priorValuePromises = offsets.map((years) => {
      if (!startDate || !endDate) return Promise.resolve(null);
      const range = shiftPeriodRangeByYears(
        { start_date: startDate, end_date: endDate },
        years,
      );
      return fetchMetric(apiMetric, {
        startDate: range.start_date,
        endDate: range.end_date,
      });
    });
    const quantityPromise = includeQuantityOverlay
      ? fetchMetric("quantity")
      : Promise.resolve(null);
    const priorQuantityPromises = includeQuantityOverlay
      ? offsets.map((years) => {
          if (!startDate || !endDate) return Promise.resolve(null);
          const range = shiftPeriodRangeByYears(
            { start_date: startDate, end_date: endDate },
            years,
          );
          return fetchMetric("quantity", {
            startDate: range.start_date,
            endDate: range.end_date,
          });
        })
      : [];

    void Promise.all([
      currentPromise,
      quantityPromise,
      ...priorValuePromises,
      ...priorQuantityPromises,
    ]).then(([currentPayload, quantityPayload, ...rest]) => {
        if (cancelled) return;
        const priorValuePayloads = rest.slice(0, offsets.length);
        const priorQuantityPayloads = includeQuantityOverlay
          ? rest.slice(offsets.length, offsets.length * 2)
          : [];
        const next = mergeBillingSeriesOverlays({
          current: currentPayload.points ?? [],
          quantityPoints: quantityPayload?.points,
          priorValueSeries: priorValuePayloads.map((payload) => payload?.points ?? []),
          priorQuantitySeries: priorQuantityPayloads.map(
            (payload) => payload?.points ?? [],
          ),
        });
        setPoints(next);
        setCoverage(currentPayload.coverage);
        setError(currentPayload.partialError);
        const quantityMeta = includeQuantityOverlay
          ? quantityPayload
          : apiMetric === "quantity"
            ? currentPayload
            : null;
        const nextUnit = (quantityMeta?.unit || "").trim();
        setQuantityUnit(nextUnit || null);
        setQuantityMixedUnits(Boolean(quantityMeta?.mixed_units));
      })
      .catch((err: unknown) => {
        if (cancelled || controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar o gráfico.";
        setError(message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [
    enabled,
    fingerprint,
    reloadKey,
    startDate,
    endDate,
    granularity,
    compareYears,
    nature,
    metric,
    productCodesKey,
    productGroupsKey,
    market,
  ]);

  const displayedPoints = useMemo(
    () => (enabled && fingerprint ? points : []),
    [enabled, fingerprint, points],
  );
  const totalValue = useMemo(
    () => displayedPoints.reduce((sum, point) => sum + (Number(point.value) || 0), 0),
    [displayedPoints],
  );
  const totalQuantity = useMemo(
    () => displayedPoints.reduce((sum, point) => sum + (Number(point.quantity) || 0), 0),
    [displayedPoints],
  );

  return {
    selectedKeys: effectiveSelectedKeys,
    setSelectedKeys,
    customerOptions,
    points: displayedPoints,
    loading: enabled && fingerprint ? loading : false,
    error: enabled && fingerprint ? error : null,
    totalValue,
    totalQuantity,
    quantityUnit: enabled && fingerprint ? quantityUnit : null,
    quantityMixedUnits: enabled && fingerprint ? quantityMixedUnits : false,
    coverage:
      enabled && fingerprint ? coverage : { covered: 0, total: 0, failedBatches: 0 },
    reload,
  };
}
