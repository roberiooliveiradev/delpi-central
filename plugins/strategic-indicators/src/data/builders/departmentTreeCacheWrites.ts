import type { DepartmentOverviewViewItem } from "../types/departments";
import type { IndicatorViewItem } from "../types/indicators";
import {
  buildStrategicIndicatorsCacheKey,
  setStrategicIndicatorsCachedValue,
} from "../cache/strategicIndicatorsReadCache";

type CacheQuery = {
  competence?: string;
  startDate?: string;
  endDate?: string;
};

export function writeDepartmentsReadCache(
  query: CacheQuery,
  branch: string | undefined,
  departments: DepartmentOverviewViewItem[],
): void {
  setStrategicIndicatorsCachedValue(
    buildStrategicIndicatorsCacheKey("departments", {
      competence: query.competence,
      branch,
      startDate: query.startDate,
      endDate: query.endDate,
    }),
    departments,
  );
}

export function writeIndicatorsReadCache(
  query: CacheQuery,
  branch: string | undefined,
  items: IndicatorViewItem[],
): void {
  setStrategicIndicatorsCachedValue(
    buildStrategicIndicatorsCacheKey("indicators", {
      competence: query.competence,
      branch,
      startDate: query.startDate,
      endDate: query.endDate,
    }),
    {
      items,
      fetchErrors: [],
      partialSuccess: false,
    },
  );
}
