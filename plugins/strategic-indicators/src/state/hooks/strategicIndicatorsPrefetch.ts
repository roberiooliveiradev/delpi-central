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

/** Evita competir com a requisição principal (executive-summary / árvore). */
const PREFETCH_DELAY_MS = 3000;

function schedulePrefetch(run: () => void): void {
  const timeoutId = window.setTimeout(run, PREFETCH_DELAY_MS);
  const cancel = () => window.clearTimeout(timeoutId);
  if (typeof window !== "undefined") {
    window.addEventListener("pagehide", cancel, { once: true });
  }
}

export function prefetchStrategicIndicatorsDepartments(
  params: PrefetchParams,
): void {
  schedulePrefetch(() => {
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
  });
}

export function prefetchStrategicIndicatorsTrends(
  params: PrefetchParams,
): void {
  const months = params.months ?? 3;
  const cacheKey = buildStrategicIndicatorsCacheKey("trends", {
    competence: params.competence,
    branch: params.branch,
    startDate: params.startDate,
    endDate: params.endDate,
    months,
  });

  schedulePrefetch(() => {
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
  });
}
