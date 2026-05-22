import type { TrendsDashboardViewData } from "../types/trends";
import type {
  DepartmentTreeModel,
  DepartmentTreeScopeKey,
  DepartmentTreeSparkPoint,
} from "../types/departmentTree";

function trimSeries(
  points: DepartmentTreeSparkPoint[],
  months: number,
): DepartmentTreeSparkPoint[] {
  if (months <= 0 || points.length <= months) {
    return points;
  }

  return points.slice(-months);
}

function mapDepartmentSeries(
  trends: TrendsDashboardViewData | null | undefined,
  departmentId: string,
  months: number,
): DepartmentTreeSparkPoint[] {
  const department = trends?.departments.find((item) => item.id === departmentId);
  if (!department?.series?.length) {
    return [];
  }

  return trimSeries(
    department.series.map((point) => ({
      period: point.period,
      value: point.score,
    })),
    months,
  );
}

function mapIndicatorSeries(
  trends: TrendsDashboardViewData | null | undefined,
  departmentId: string,
  indicatorId: string,
  months: number,
): DepartmentTreeSparkPoint[] {
  const indicators = trends?.indicatorSeriesByDepartmentId?.[departmentId] ?? [];
  const match = indicators.find((item) => item.indicatorId === indicatorId);
  if (!match?.series?.length) {
    return [];
  }

  return trimSeries(
    match.series.map((point) => ({
      period: point.period,
      value: point.score,
    })),
    months,
  );
}

function mapIgdSeries(
  trends: TrendsDashboardViewData | null | undefined,
  months: number,
): DepartmentTreeSparkPoint[] {
  if (!trends?.igdSeries?.length) {
    return [];
  }

  return trimSeries(
    trends.igdSeries.map((point) => ({
      period: point.period,
      value: point.value,
    })),
    months,
  );
}

export function enrichDepartmentTreeWithTrends(
  model: DepartmentTreeModel,
  trendsByScope: Partial<Record<DepartmentTreeScopeKey, TrendsDashboardViewData>>,
  months: number,
): DepartmentTreeModel {
  const primaryTrends =
    trendsByScope.consolidated ??
    trendsByScope["01"] ??
    trendsByScope["02"] ??
    null;

  return {
    ...model,
    trendMonths: months,
    igdSeries: mapIgdSeries(primaryTrends, months),
    columns: model.columns.map((column) => {
      const scopeTrends = trendsByScope[column.scope.key] ?? primaryTrends;

      return {
        ...column,
        departments: column.departments.map((node) => ({
          ...node,
          series: mapDepartmentSeries(scopeTrends, node.department.id, months),
          indicators: node.indicators.map((indicatorNode) => ({
            ...indicatorNode,
            series: mapIndicatorSeries(
              scopeTrends,
              node.department.id,
              indicatorNode.indicator.id,
              months,
            ),
          })),
        })),
      };
    }),
  };
}
