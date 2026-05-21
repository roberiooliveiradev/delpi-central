import type { TrendsDashboardViewData } from "../types/trends";
import type {
  DepartmentTreeModel,
  DepartmentTreeScopeKey,
  DepartmentTreeSparkPoint,
} from "../types/departmentTree";

function mapDepartmentSeries(
  trends: TrendsDashboardViewData | null | undefined,
  departmentId: string,
): DepartmentTreeSparkPoint[] {
  const department = trends?.departments.find((item) => item.id === departmentId);
  if (!department?.series?.length) {
    return [];
  }

  return department.series.map((point) => ({
    period: point.period,
    value: point.score,
  }));
}

function mapIndicatorSeries(
  trends: TrendsDashboardViewData | null | undefined,
  departmentId: string,
  indicatorId: string,
): DepartmentTreeSparkPoint[] {
  const indicators = trends?.indicatorSeriesByDepartmentId?.[departmentId] ?? [];
  const match = indicators.find((item) => item.indicatorId === indicatorId);
  if (!match?.series?.length) {
    return [];
  }

  return match.series.map((point) => ({
    period: point.period,
    value: point.score,
  }));
}

function mapIgdSeries(
  trends: TrendsDashboardViewData | null | undefined,
): DepartmentTreeSparkPoint[] {
  if (!trends?.igdSeries?.length) {
    return [];
  }

  return trends.igdSeries.map((point) => ({
    period: point.period,
    value: point.value,
  }));
}

export function enrichDepartmentTreeWithTrends(
  model: DepartmentTreeModel,
  trendsByScope: Partial<Record<DepartmentTreeScopeKey, TrendsDashboardViewData>>,
): DepartmentTreeModel {
  const primaryTrends =
    trendsByScope.consolidated ??
    trendsByScope["01"] ??
    trendsByScope["02"] ??
    null;

  return {
    ...model,
    igdSeries: mapIgdSeries(primaryTrends),
    columns: model.columns.map((column) => {
      const scopeTrends = trendsByScope[column.scope.key] ?? primaryTrends;

      return {
        ...column,
        departments: column.departments.map((node) => ({
          ...node,
          series: mapDepartmentSeries(scopeTrends, node.department.id),
          indicators: node.indicators.map((indicatorNode) => ({
            ...indicatorNode,
            series: mapIndicatorSeries(
              scopeTrends,
              node.department.id,
              indicatorNode.indicator.id,
            ),
          })),
        })),
      };
    }),
  };
}
