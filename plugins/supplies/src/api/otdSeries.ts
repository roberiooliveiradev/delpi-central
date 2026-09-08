import { httpGet, suppliesApiUrl } from "./httpClient";

export type OtdSeriesPoint = {
  period: string;
  otdPct: number | null;
  onTime: number | null;
  total: number | null;
};

export type OtdSeriesResponse = {
  scope: {
    branches: string[];
    mode: "single" | "consolidated";
  };
  period: {
    from: string;
    to: string;
    label: string;
  };
  granularity: string;
  points: OtdSeriesPoint[];
  partialFailures: Array<{ source?: string; message: string }>;
};

export type OtdSeriesQuery = {
  branch?: string;
  from?: string;
  to?: string;
  granularity?: "month" | "week" | "day";
};

export function buildOtdSeriesQuery(params: OtdSeriesQuery): string {
  const search = new URLSearchParams();
  if (params.branch) search.set("branch", params.branch);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  if (params.granularity) search.set("granularity", params.granularity);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function getOtdSeries(
  params: OtdSeriesQuery = {},
  signal?: AbortSignal,
): Promise<OtdSeriesResponse> {
  return httpGet<OtdSeriesResponse>(
    suppliesApiUrl(`/analytics/otd/series${buildOtdSeriesQuery(params)}`),
    { signal },
  );
}
