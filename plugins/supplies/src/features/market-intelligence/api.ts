/** Market intelligence BFF client (PROC-0076).

Thin adapter over `httpClient` — all business semantics (FX conversion,
averages, coverage, freshness) are decided by the supplies-api BFF; the
MFE renders what the contract delivers and never recalculates.
*/

import { httpGet, suppliesApiUrl } from "../../api/httpClient";

export type MarketInstrumentKind = "metal" | "fx";
export type MarketCurrency = "USD" | "BRL";
export type MarketGranularity = "day" | "month" | "year";
export type MarketFxKind = "ptax_closing_sell" | "ptax_closing_buy";
export type MarketDataStatus = "ok" | "no_data" | "stale" | "partial";

/** Feed-level freshness evaluated by the BFF against the provider's real
publication cadence — never against the queried window. */
export type MarketFreshness = {
  status: "current" | "delayed" | "unknown";
  expected_cadence: "monthly" | "business_daily";
  expected_latest_period: string;
  latest_observation_date: string | null;
  lag_periods?: number | null;
  lag_days?: number | null;
  last_successful_ingestion_at: string | null;
  evaluation_date: string;
  method: string;
};

export type MarketInstrumentFilter = {
  code: string;
  kind: MarketInstrumentKind;
  label: string;
  unit: string | null;
  currency: MarketCurrency;
  quote_basis: string | null;
  granularities: MarketGranularity[];
  currencies: MarketCurrency[];
  latest_observation_date: string | null;
  source_id: string;
};

export type MarketSourceMeta = {
  source_id: string;
  provider_id: string;
  attribution: string;
  license_reference: string;
};

export type MarketFiltersResponse = {
  instruments: MarketInstrumentFilter[];
  currencies: MarketCurrency[];
  granularities: MarketGranularity[];
  fx_kinds: MarketFxKind[];
  default_fx_kind: MarketFxKind;
  default_instrument: string | null;
  sources: MarketSourceMeta[];
  meta: {
    data_status: MarketDataStatus;
    schema_version: string;
    last_successful_ingestion_at: string | null;
  };
};

export type MarketSummaryResponse = {
  instrument: {
    code: string;
    kind: MarketInstrumentKind;
    label: string;
    unit: string | null;
    quote_basis: string | null;
  };
  last_quote: {
    value: string | null;
    reference_date: string;
    currency: MarketCurrency;
    /** Display unit — BRL/metric ton when converted, USD/metric ton natively. */
    unit: string | null;
    /** Original source values — audit trail, present on converted quotes. */
    native?: { value: string | null; currency: string; unit: string | null };
    conversion?: {
      method: string;
      fx_kind: string;
      fx_rate: string | null;
      fx_reference_period: string;
    };
  } | null;
  period_average: {
    value: string | null;
    valid_observations: number;
    coverage: string;
    unit: string | null;
    method: string;
  };
  period_variation: {
    percent: string | null;
    calculation_method: string;
  };
  fx_reference: {
    value: string | null;
    pair: string;
    rate_kind: string;
    reference_date: string | null;
  };
  meta: {
    data_status: MarketDataStatus;
    source_id: string | null;
    currency: MarketCurrency;
    unit: string | null;
    native_unit: string | null;
    freshness: MarketFreshness;
    method_version: Record<string, string | null>;
    partial_reason: string | null;
    last_successful_ingestion_at: string | null;
  };
};

export type MarketSeriesPoint = {
  period: string;
  value: string | null;
  observation_count: number;
  expected_observations?: number;
  coverage: string;
};

export type MarketSeriesResponse = {
  instrument: MarketSummaryResponse["instrument"];
  currency: MarketCurrency;
  unit: string | null;
  native_unit: string | null;
  granularity: MarketGranularity;
  points: MarketSeriesPoint[];
  meta: {
    source_id: string | null;
    fx_source_id: string | null;
    fx_kind: MarketFxKind | null;
    freshness: MarketFreshness;
    method_version: Record<string, string | null>;
    data_status: MarketDataStatus;
    partial_reason: string | null;
    schema_version: string;
    last_successful_ingestion_at: string | null;
  };
};

export type MarketMonthlyAverageRow = {
  period: string;
  average: string | null;
  native_average: string | null;
  observation_count: number;
  coverage: string;
  fx_rate: string | null;
  period_start: string;
  period_end: string;
};

export type MarketMonthlyAveragesResponse = {
  instrument: MarketSummaryResponse["instrument"];
  currency: MarketCurrency;
  unit: string | null;
  native_unit: string | null;
  items: MarketMonthlyAverageRow[];
  page_info: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_more: boolean;
  };
  meta: MarketSeriesResponse["meta"];
};

export type MarketQueryParams = {
  instrument: string;
  currency: MarketCurrency;
  fx_kind: MarketFxKind;
  date_from: string;
  date_to: string;
};

function toQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function getMarketIntelligenceFilters(
  signal?: AbortSignal,
): Promise<MarketFiltersResponse> {
  return httpGet(suppliesApiUrl("/market-intelligence/filters"), { signal });
}

export function getMarketIntelligenceSummary(
  params: MarketQueryParams,
  signal?: AbortSignal,
): Promise<MarketSummaryResponse> {
  return httpGet(
    suppliesApiUrl(`/market-intelligence/summary${toQuery(params)}`),
    { signal },
  );
}

export function getMarketIntelligenceSeries(
  params: MarketQueryParams & { granularity: MarketGranularity },
  signal?: AbortSignal,
): Promise<MarketSeriesResponse> {
  return httpGet(
    suppliesApiUrl(`/market-intelligence/series${toQuery(params)}`),
    { signal },
  );
}

export function getMarketIntelligenceMonthlyAverages(
  params: MarketQueryParams & { page?: number; page_size?: number },
  signal?: AbortSignal,
): Promise<MarketMonthlyAveragesResponse> {
  return httpGet(
    suppliesApiUrl(`/market-intelligence/monthly-averages${toQuery(params)}`),
    { signal },
  );
}
