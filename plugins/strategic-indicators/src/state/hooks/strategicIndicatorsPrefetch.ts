import { adaptDepartmentsToView } from "../../data/adapters/departmentsAdapter";
import { adaptTrendsToView } from "../../data/adapters/trendsAdapter";
import { fetchStrategicIndicatorsDepartments } from "../../data/api/strategicIndicatorsDepartmentsApi";
import { writeDepartmentsReadCache } from "../../data/builders/departmentTreeCacheWrites";
import { fetchStrategicIndicatorsTrends } from "../../data/api/strategicIndicatorsTrendsApi";
import {
  buildStrategicIndicatorsCacheKey,
  setStrategicIndicatorsCachedValue,
} from "../../data/cache/strategicIndicatorsReadCache";
import type { TrendsDashboardViewData } from "../../data/types/trends";

type PrefetchParams = {
  competence?: string;
  branch?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
  getAccessToken?: () => string | undefined;
};

export function prefetchStrategicIndicatorsDepartments(
  params: PrefetchParams,
): void {
  void fetchStrategicIndicatorsDepartments({
    competence: params.competence,
    branch: params.branch,
    startDate: params.startDate,
    endDate: params.endDate,
    getAccessToken: params.getAccessToken,
  })
    .then((response) => {
      writeDepartmentsReadCache(
        {
          competence: params.competence,
          startDate: params.startDate,
          endDate: params.endDate,
        },
        params.branch,
        adaptDepartmentsToView(response),
      );
    })
    .catch(() => undefined);
}

export function prefetchStrategicIndicatorsTrends(
  params: PrefetchParams,
): void {
  const months = params.months ?? 6;
  const cacheKey = buildStrategicIndicatorsCacheKey("trends", {
    competence: params.competence,
    branch: params.branch,
    startDate: params.startDate,
    endDate: params.endDate,
    months,
  });

  void fetchStrategicIndicatorsTrends({
    competence: params.competence,
    branch: params.branch,
    startDate: params.startDate,
    endDate: params.endDate,
    months,
    getAccessToken: params.getAccessToken,
  })
    .then((response) => {
      const viewData = adaptTrendsToView(response);
      setStrategicIndicatorsCachedValue<TrendsDashboardViewData>(
        cacheKey,
        viewData,
      );
    })
    .catch(() => undefined);
}
