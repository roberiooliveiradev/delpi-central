import { adaptDepartmentsToView } from "./departmentsAdapter";
import { adaptIndicatorsToView } from "./indicatorsAdapter";
import { adaptTrendsToView } from "./trendsAdapter";
import { buildDepartmentTreeModel } from "../builders/buildDepartmentTreeModel";
import { enrichDepartmentTreeWithTrends } from "../builders/enrichDepartmentTreeWithTrends";
import type { DepartmentTreeScopeConfig, DepartmentTreeModel } from "../types/departmentTree";
import type {
  StrategicIndicatorsDepartmentTreeResponse,
  StrategicIndicatorsDepartmentTreeScopeApi,
} from "../types/departmentTreeBundle";
import type { DepartmentTreeScopeKey } from "../types/departmentTree";
import type { TrendsDashboardViewData } from "../types/trends";

function mapScopeConfig(scope: StrategicIndicatorsDepartmentTreeScopeApi): DepartmentTreeScopeConfig {
  return {
    key: scope.scope_key,
    branch: scope.branch ?? undefined,
    label: scope.scope_label,
  };
}

export function adaptDepartmentTreeBundleToModel(
  response: StrategicIndicatorsDepartmentTreeResponse,
): DepartmentTreeModel {
  const scopePayloads = response.scopes.map((scope) => ({
    scope: mapScopeConfig(scope),
    departments: adaptDepartmentsToView(scope.departments),
    indicators: adaptIndicatorsToView(scope.indicators),
    trends: adaptTrendsToView(scope.trends),
  }));

  const baseModel = buildDepartmentTreeModel({
    competence: response.competence,
    igd: response.igd,
    igdExact: response.igd_exact,
    classification: response.classification,
    scopePayloads,
  });

  const trendsByScope = scopePayloads.reduce<
    Partial<Record<DepartmentTreeScopeKey, TrendsDashboardViewData>>
  >((accumulator, item) => {
    accumulator[item.scope.key] = item.trends;
    return accumulator;
  }, {});

  return enrichDepartmentTreeWithTrends(baseModel, trendsByScope);
}
