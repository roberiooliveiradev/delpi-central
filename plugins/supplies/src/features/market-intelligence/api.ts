/** Market intelligence BFF client (PROC-0076).

Thin adapter over `httpClient` — all business semantics (FX conversion,
averages, coverage, freshness) are decided by the supplies-api BFF; the
MFE renders what the contract delivers and never recalculates.
*/

import { httpGet, suppliesApiUrl } from "../../api/httpClient";

export type MarketInstrumentKind = "metal" | "fx";
export type MarketCurrency = "USD" | "BRL";
export type MarketGranularity = "day" | "week" | "month" | "year";
export type MarketFxKind = "ptax_closing_sell" | "ptax_closing_buy";
// Window-completeness only (R1.1): feed delay is a separate
// dimension reported by MarketFreshness.status === "delayed" —
// never conflated into data_status.
export type MarketDataStatus = "ok" | "no_data" | "partial";

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
  /** False when the source's recorded rights don't cover display —
  non-selectable in the UI (R1.2 quarantine). */
  selectable?: boolean;
  /** R4 D-04: catalog presence keeps the card selectable in the UI —
  visual selection is never data authorization. */
  selectable_in_ui?: boolean;
  /** R4 D-04: only an explicit display grant allows reading values. */
  data_access_allowed?: boolean;
};

export type MarketSourceMeta = {
  source_id: string;
  provider_id: string;
  attribution: string;
  license_reference: string;
};

/** Approved import NCM offered by the R2 catalog (MDIC Comex Stat). */
export type MarketImportNcmFilter = {
  ncm_code: string;
  kind: "comex_import";
  description: string;
  family_code: string | null;
  ncm_version: string | null;
  unit: string;
  granularities: MarketGranularity[];
  source_id: string;
  latest_observation_date: string | null;
  selectable?: boolean;
};

/** IBGE SIDRA producer-price series (IPP Metalurgia). */
export type MarketProducerPriceFilter = {
  series_id: string;
  kind: "producer_price";
  label: string;
  activity_code: string;
  activity_label: string;
  variable_code: string;
  variable_label: string;
  table_code: string;
  metric_kind: string;
  unit: string;
  base_reference: string | null;
  granularities: MarketGranularity[];
  source_id: string;
  latest_observation_date: string | null;
  selectable?: boolean;
};

export type MarketFiltersResponse = {
  instruments: MarketInstrumentFilter[];
  import_ncms?: MarketImportNcmFilter[];
  producer_price_series?: MarketProducerPriceFilter[];
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

/** Per-feed ingestion evidence surfaced by the BFF meta (R3). */
export type MarketFeedIngestion = {
  feed: string;
  last_run_outcome: string | null;
  last_error_code: string | null;
  source_active: boolean | null;
  last_successful_at: string | null;
  latest_observation_date: string | null;
};

/** Reason an active perspective has no observations — feed evidence,
 * never a UI guess (R3). */
export type MarketUnavailableReason =
  | "provider_unavailable"
  | "feed_failed"
  | "feed_disabled"
  | "feed_not_collected"
  | "window_empty";

/** Contextual KPI read model computed by the BFF for the selected
 * series — never a quotation card repurposed for another metric. */
export type MarketSeriesSummary = {
  latest: { period: string; value: string } | null;
  period_average: string | null;
  period_change_pct: string | null;
  period_min: { period: string; value: string } | null;
  period_max: { period: string; value: string } | null;
  totals: {
    fob_usd_total: string | null;
    net_weight_t: string | null;
  } | null;
  observed: number;
  expected: number;
  coverage: string;
  missing_periods: string[] | null;
  unavailable_reason: MarketUnavailableReason | null;
  method_version: Record<string, string | null>;
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
    feed_ingestion?: MarketFeedIngestion | null;
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

/** One aggregated month/year of Comex import data for an approved NCM. */
export type MarketImportPoint = {
  period: string;
  fob_usd_total: string | null;
  net_weight_kg_total: string | null;
  net_weight_t: string | null;
  unit_value_usd_per_t: string | null;
  contributing_rows: number;
  observation_count: number;
  coverage: string;
};

export type MarketImportSeriesResponse = {
  series: {
    ncm_code: string;
    ncm_version: string | null;
    description: string;
    family_code: string | null;
    kind: "comex_import";
    unit: string;
    metric_kind: string;
  };
  filters: { country_code: string | null; state_code: string | null };
  granularity: MarketGranularity;
  points: MarketImportPoint[];
  summary?: MarketSeriesSummary;
  meta: MarketSeriesResponse["meta"];
};

export type MarketProducerPricePoint = {
  period: string;
  value: string | null;
  quality?: string | null;
  observation_count: number;
  coverage: string;
};

export type MarketProducerPriceSeriesResponse = {
  series: {
    series_id: string;
    kind: "producer_price";
    label: string;
    activity_code: string;
    activity_label: string;
    variable_code: string;
    variable_label: string;
    table_code: string;
    metric_kind: string;
    unit: string;
    base_reference: string | null;
  };
  granularity: MarketGranularity;
  points: MarketProducerPricePoint[];
  summary?: MarketSeriesSummary;
  meta: MarketSeriesResponse["meta"];
};

export type MarketFxSeriesResponse = {
  series: {
    instrument_code: string;
    kind: "fx";
    label: string;
    pair: string;
    rate_kind: MarketFxKind;
    unit: string;
  };
  granularity: MarketGranularity;
  points: MarketSeriesPoint[];
  summary?: MarketSeriesSummary;
  meta: MarketSeriesResponse["meta"];
};

export type MarketQueryParams = {
  instrument: string;
  currency: MarketCurrency;
  fx_kind: MarketFxKind;
  date_from: string;
  date_to: string;
};

/** R4 D-04 availability — catalog facts separate from data rights. */
export type MarketQuoteAvailability = {
  selectable_in_ui: boolean;
  data_access_allowed: boolean;
  observations_available: boolean;
  source_id: string | null;
  unavailable_reason:
    | "source_use_pending"
    | MarketUnavailableReason
    | null;
};

export type MarketQuoteSeriesEntry = {
  instrument: {
    code: string;
    kind: MarketInstrumentKind;
    label: string;
    unit: string | null;
    quote_basis: string | null;
  };
  unit: string | null;
  currency?: MarketCurrency;
  availability: MarketQuoteAvailability;
  points: MarketSeriesPoint[];
  summary: MarketSeriesSummary | null;
  meta?: MarketSeriesResponse["meta"];
};

export type MarketQuoteSeriesResponse = {
  granularity: MarketGranularity;
  currency: MarketCurrency;
  series: MarketQuoteSeriesEntry[];
  meta: {
    data_status: MarketDataStatus;
    schema_version: string;
    feed_ingestion?: MarketFeedIngestion | null;
    last_successful_ingestion_at: string | null;
  };
};

export type MarketQuoteCompareResponse = {
  comparison: {
    comparable: boolean;
    reason: "insufficient_authorized_series" | "incompatible_units" | null;
    unit: string | null;
    granularity: MarketGranularity;
    currency: MarketCurrency;
    method: string;
  };
  periods: string[];
  series: {
    instrument: MarketQuoteSeriesEntry["instrument"];
    unit: string | null;
    availability: MarketQuoteAvailability;
    summary?: MarketSeriesSummary | null;
    values: (string | null)[] | null;
  }[];
  meta: MarketQuoteSeriesResponse["meta"];
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

export function getMarketImportSeries(
  params: {
    ncm: string;
    granularity: MarketGranularity;
    date_from: string;
    date_to: string;
    country_code?: string;
    state_code?: string;
  },
  signal?: AbortSignal,
): Promise<MarketImportSeriesResponse> {
  return httpGet(
    suppliesApiUrl(`/market-intelligence/imports/series${toQuery(params)}`),
    { signal },
  );
}

export function getMarketProducerPriceSeries(
  params: {
    series_id: string;
    granularity: MarketGranularity;
    date_from: string;
    date_to: string;
  },
  signal?: AbortSignal,
): Promise<MarketProducerPriceSeriesResponse> {
  return httpGet(
    suppliesApiUrl(
      `/market-intelligence/producer-prices/series${toQuery(params)}`,
    ),
    { signal },
  );
}

export function getMarketQuoteSeries(
  params: {
    instruments: string;
    granularity: MarketGranularity;
    currency?: MarketCurrency;
    fx_kind?: MarketFxKind;
    date_from: string;
    date_to: string;
  },
  signal?: AbortSignal,
): Promise<MarketQuoteSeriesResponse> {
  return httpGet(
    suppliesApiUrl(`/market-intelligence/quotes/series${toQuery(params)}`),
    { signal },
  );
}

export function getMarketQuoteCompare(
  params: {
    instruments: string;
    granularity: MarketGranularity;
    currency?: MarketCurrency;
    fx_kind?: MarketFxKind;
    date_from: string;
    date_to: string;
  },
  signal?: AbortSignal,
): Promise<MarketQuoteCompareResponse> {
  return httpGet(
    suppliesApiUrl(
      `/market-intelligence/quotes/compare${toQuery(params)}`,
    ),
    { signal },
  );
}

export function getMarketFxSeries(
  params: {
    fx_kind: MarketFxKind;
    granularity: MarketGranularity;
    date_from: string;
    date_to: string;
  },
  signal?: AbortSignal,
): Promise<MarketFxSeriesResponse> {
  return httpGet(
    suppliesApiUrl(`/market-intelligence/fx/series${toQuery(params)}`),
    { signal },
  );
}
