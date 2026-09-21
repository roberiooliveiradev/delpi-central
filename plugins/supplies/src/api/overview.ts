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
  /** @deprecated Prefer comparableGoal — period-comparable meta. */
  meta: number | null;
  goalValue: number | null;
  comparableGoal: number | null;
  referenceGoal: number | null;
  /** Nota IDD canônica do SI (`score`); null quando SI não enviou. */
  iddScore: number | null;
  performanceDirection: "higher_is_better" | "lower_is_better" | null;
  goalMode: string | null;
  status: OverviewKpiStatus;
  source: string;
  strategic?: OverviewKpiStrategic | null;
};

export type OverviewUnitValueMap = {
  consolidated?: number | null;
  "01"?: number | null;
  "02"?: number | null;
};

export type OverviewKpiStrategic = {
  indicatorId: string | null;
  score: number | null;
  realized: OverviewUnitValueMap;
  goals: OverviewUnitValueMap;
  goalValue: number | null;
  comparableGoal: number | null;
  referenceGoal: number | null;
  goalMode: string | null;
  goalPeriodKind: string | null;
  goalPeriodPartial: boolean | null;
  performanceDirection: "higher_is_better" | "lower_is_better" | null;
  valueUnit: string | null;
  valuePrefix: string | null;
  valueSuffix: string | null;
  valueDecimals: number | null;
};

export type OverviewDepartmentScore = {
  score: number | null;
  classification: string | null;
};

export type OverviewStrategicContext = {
  departmentId: string;
  scope?: {
    mode: "single" | "consolidated";
    branches: string[];
    key: "consolidated" | "01" | "02";
    label: string;
  };
  score?: OverviewDepartmentScore;
  scores: {
    consolidated?: OverviewDepartmentScore;
    "01"?: OverviewDepartmentScore;
    "02"?: OverviewDepartmentScore;
  };
  partialSuccess: boolean;
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
  strategicContext?: OverviewStrategicContext;
  siValueDrift?: Array<{
    kpiId: string;
    scope: string;
    operationalValue: number;
    siValue: number;
    period: { from: string; to: string };
  }>;
};

export type OverviewQuery = {
  branches?: string[];
  from?: string;
  to?: string;
};

function buildQuery(params: OverviewQuery): string {
  const search = new URLSearchParams();
  for (const branch of params.branches ?? []) {
    if (branch) search.append("branch", branch);
  }
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
