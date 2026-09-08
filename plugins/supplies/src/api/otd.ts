import { httpGet, suppliesApiUrl } from "./httpClient";

export type OtdBranchAggregate = {
  otdPct: number | null;
  goal: number | null;
  onTime: number | null;
  total: number | null;
};

export type OtdAggregateResponse = {
  scope: {
    branches: string[];
    mode: "single" | "consolidated";
  };
  period: {
    from: string;
    to: string;
    label: string;
  };
  otdPct: number | null;
  goal: number | null;
  onTime: number | null;
  total: number | null;
  byBranch: Record<string, OtdBranchAggregate>;
  partialFailures: Array<{ source?: string; branch?: string; message: string }>;
};

export type OtdAggregateQuery = {
  branch?: string;
  from?: string;
  to?: string;
};

export function buildOtdAggregateQuery(params: OtdAggregateQuery): string {
  const search = new URLSearchParams();
  if (params.branch) search.set("branch", params.branch);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function getOtdAggregate(
  params: OtdAggregateQuery = {},
  signal?: AbortSignal,
): Promise<OtdAggregateResponse> {
  return httpGet<OtdAggregateResponse>(
    suppliesApiUrl(`/analytics/otd${buildOtdAggregateQuery(params)}`),
    { signal },
  );
}
