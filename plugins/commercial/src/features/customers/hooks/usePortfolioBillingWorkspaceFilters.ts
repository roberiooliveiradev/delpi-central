import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { CustomerSummary } from "../types/customerSummary";
import {
  DEFAULT_BILLING_SERIES_PRESET,
  periodRangeFromBillingPreset,
  type BillingSeriesPeriodPreset,
} from "../utils/billingSeriesPeriod";
import { validateBillingPeriod } from "../billing/utils/billingPeriod";

export type BillingMarketFilter = "domestic" | "export";

export type BillingSeriesCustomerOption = {
  key: string;
  codigo: string;
  loja: string;
  nome: string;
};

export type PortfolioBillingWorkspaceFilters = {
  preset: BillingSeriesPeriodPreset;
  setPreset: (preset: BillingSeriesPeriodPreset) => void;
  customStart: string;
  customEnd: string;
  setCustomStart: (value: string) => void;
  setCustomEnd: (value: string) => void;
  startDate: string;
  endDate: string;
  periodError: string | null;
  selectedCustomerKeys: string[];
  setSelectedCustomerKeys: (keys: string[]) => void;
  customerOptions: BillingSeriesCustomerOption[];
  /** CSV de códigos TOTVS (vazio = toda a carteira no BFF). */
  customerCodesCsv: string;
  customerCenters: string[];
  setCustomerCenters: (centers: string[]) => void;
  /** CSV de centros (vazio = omitido). */
  customerCentersCsv: string;
  selectedProductCodes: string[];
  setSelectedProductCodes: (codes: string[]) => void;
  selectedProductGroups: string[];
  setSelectedProductGroups: (groups: string[]) => void;
  selectedMarkets: BillingMarketFilter[];
  setSelectedMarkets: (markets: BillingMarketFilter[]) => void;
  /** Um mercado só → param; vazio ou ambos → undefined. */
  marketParam: BillingMarketFilter | undefined;
  productCodesCsv: string;
  productGroupsCsv: string;
  clearProductAndMarketFilters: () => void;
  /** Limpa cliente/família/produto/mercado (mantém período). */
  clearRecorteFilters: () => void;
  hasActiveRecorteFilters: boolean;
};

function customerOptionsFromList(
  customers: CustomerSummary[] | undefined,
): BillingSeriesCustomerOption[] {
  return (customers ?? [])
    .map((customer) => ({
      key: customer.key,
      codigo: customer.codigo,
      loja: customer.loja,
      nome: customer.nome,
    }))
    .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
}

const BILLING_CUSTOMER_CENTERS_SESSION_KEY = "delpi.commercial.billing.customerCenters";

function readStoredCustomerCenters(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(BILLING_CUSTOMER_CENTERS_SESSION_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    const seen = new Set<string>();
    const out: string[] = [];
    for (const entry of parsed) {
      if (typeof entry !== "string") continue;
      const center = entry.trim();
      if (!center || seen.has(center)) continue;
      seen.add(center);
      out.push(center);
    }
    return out;
  } catch {
    return [];
  }
}

function writeStoredCustomerCenters(centers: string[]): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(
      BILLING_CUSTOMER_CENTERS_SESSION_KEY,
      JSON.stringify(centers),
    );
  } catch {
    // ignora
  }
}

/**
 * Estado único de filtros do painel Faturamento (série + tabelas).
 */
export function usePortfolioBillingWorkspaceFilters(
  customers: CustomerSummary[] | undefined,
  sellerId?: string | null,
): PortfolioBillingWorkspaceFilters {
  const defaultRange = periodRangeFromBillingPreset(DEFAULT_BILLING_SERIES_PRESET);
  const [preset, setPreset] = useState<BillingSeriesPeriodPreset>(
    DEFAULT_BILLING_SERIES_PRESET,
  );
  const [customStart, setCustomStart] = useState(defaultRange.startDate);
  const [customEnd, setCustomEnd] = useState(defaultRange.endDate);
  const [selectedCustomerKeys, setSelectedCustomerKeys] = useState<string[]>([]);
  const [customerCenters, setCustomerCentersState] = useState<string[]>(
    readStoredCustomerCenters,
  );
  const [selectedProductCodes, setSelectedProductCodes] = useState<string[]>([]);
  const [selectedProductGroups, setSelectedProductGroups] = useState<string[]>([]);
  const [selectedMarkets, setSelectedMarkets] = useState<BillingMarketFilter[]>([]);

  const customerOptions = useMemo(
    () => customerOptionsFromList(customers),
    [customers],
  );
  const optionKeySet = useMemo(
    () => new Set(customerOptions.map((customer) => customer.key)),
    [customerOptions],
  );
  const effectiveCustomerKeys = useMemo(
    () => selectedCustomerKeys.filter((key) => optionKeySet.has(key)),
    [optionKeySet, selectedCustomerKeys],
  );

  useEffect(() => {
    if (selectedCustomerKeys.length === effectiveCustomerKeys.length) return;
    setSelectedCustomerKeys(effectiveCustomerKeys);
  }, [effectiveCustomerKeys, selectedCustomerKeys.length]);

  const range =
    preset === "custom"
      ? { startDate: customStart, endDate: customEnd }
      : periodRangeFromBillingPreset(preset);
  const periodError =
    preset === "custom" ? validateBillingPeriod(range.startDate, range.endDate) : null;

  const customerCodesCsv = useMemo(() => {
    if (!effectiveCustomerKeys.length) return "";
    const codes = new Set<string>();
    for (const key of effectiveCustomerKeys) {
      const match = customerOptions.find((option) => option.key === key);
      if (match?.codigo) codes.add(match.codigo);
    }
    return [...codes].join(",");
  }, [customerOptions, effectiveCustomerKeys]);

  const customerCentersCsv = customerCenters.join(",");
  const sellerScopeKey = (sellerId || "").trim();
  const previousSellerScopeKey = useRef(sellerScopeKey);

  useEffect(() => {
    writeStoredCustomerCenters(customerCenters);
  }, [customerCenters]);

  useEffect(() => {
    if (previousSellerScopeKey.current === sellerScopeKey) return;
    previousSellerScopeKey.current = sellerScopeKey;
    setCustomerCentersState([]);
  }, [sellerScopeKey]);

  const marketParam = useMemo((): BillingMarketFilter | undefined => {
    if (selectedMarkets.length === 1) return selectedMarkets[0];
    return undefined;
  }, [selectedMarkets]);

  const productCodesCsv = selectedProductCodes.join(",");
  const productGroupsCsv = selectedProductGroups.join(",");

  const clearProductAndMarketFilters = useCallback(() => {
    setSelectedProductCodes([]);
    setSelectedProductGroups([]);
    setSelectedMarkets([]);
  }, []);

  const clearRecorteFilters = useCallback(() => {
    setSelectedCustomerKeys([]);
    setCustomerCentersState([]);
    setSelectedProductCodes([]);
    setSelectedProductGroups([]);
    setSelectedMarkets([]);
  }, []);

  const hasActiveRecorteFilters =
    effectiveCustomerKeys.length > 0 ||
    customerCenters.length > 0 ||
    selectedProductCodes.length > 0 ||
    selectedProductGroups.length > 0 ||
    selectedMarkets.length > 0;

  return {
    preset,
    setPreset,
    customStart,
    customEnd,
    setCustomStart,
    setCustomEnd,
    startDate: range.startDate,
    endDate: range.endDate,
    periodError,
    selectedCustomerKeys: effectiveCustomerKeys,
    setSelectedCustomerKeys,
    customerOptions,
    customerCodesCsv,
    customerCenters,
    setCustomerCenters: setCustomerCentersState,
    customerCentersCsv,
    selectedProductCodes,
    setSelectedProductCodes,
    selectedProductGroups,
    setSelectedProductGroups,
    selectedMarkets,
    setSelectedMarkets,
    marketParam,
    productCodesCsv,
    productGroupsCsv,
    clearProductAndMarketFilters,
    clearRecorteFilters,
    hasActiveRecorteFilters,
  };
}
