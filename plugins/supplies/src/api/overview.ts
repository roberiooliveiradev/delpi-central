import { httpGet, suppliesApiUrl } from "./httpClient";

export type OverviewTemporalNature = "interval" | "snapshot" | "state";

export type OverviewKpiStatus = "available" | "unavailable";

export type OverviewKpiCard = {
  id: string;
  viewId: string;
  title: string;
  description: string;
  temporalNature: OverviewTemporalNature;
  periodLabel: string;
  value: number | null;
  displayValue: string | null;
  unit: string | null;
  meta: number | null;
  status: OverviewKpiStatus;
  source: string;
};

export type OverviewPartialFailure = {
  kpiId: string;
  source: string;
  message: string;
};

export type OverviewResponse = {
  scope: {
    branches: string[];
    mode: "single" | "consolidated";
  };
  period: {
    from: string;
    to: string;
    label: string;
  };
  kpis: OverviewKpiCard[];
  partialFailures: OverviewPartialFailure[];
};

export type OverviewQuery = {
  branch?: string;
  from?: string;
  to?: string;
};

function buildQuery(params: OverviewQuery): string {
  const search = new URLSearchParams();
  if (params.branch) search.set("branch", params.branch);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function getOverview(
  params: OverviewQuery = {},
  signal?: AbortSignal,
): Promise<OverviewResponse> {
  return httpGet<OverviewResponse>(
    suppliesApiUrl(`/analytics/overview${buildQuery(params)}`),
    { signal },
  );
}
