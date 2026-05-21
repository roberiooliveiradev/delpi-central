import type { ExecutiveDashboardViewData } from "../types/executiveSummary";
import type { DepartmentOverviewViewItem } from "../types/departments";
import type { IndicatorViewItem } from "../types/indicators";
import type { DepartmentTreeScopeConfig } from "../types/departmentTree";
import type { StrategicIndicatorsViewMode } from "../../ui/shared/strategicIndicatorsFilters";
import {
  buildStrategicIndicatorsCacheKey,
  getStrategicIndicatorsCachedValue,
} from "../cache/strategicIndicatorsReadCache";
import { buildDepartmentTreeModel, type DepartmentTreeScopePayload } from "./buildDepartmentTreeModel";
import type { DepartmentTreeModel } from "../types/departmentTree";

type ReadCacheQuery = {
  competence?: string;
  startDate?: string;
  endDate?: string;
};

type IndicatorsReadCache = {
  items: IndicatorViewItem[];
};

function getCachedDepartments(
  query: ReadCacheQuery,
  branch?: string,
): DepartmentOverviewViewItem[] | null {
  return getStrategicIndicatorsCachedValue<DepartmentOverviewViewItem[]>(
    buildStrategicIndicatorsCacheKey("departments", {
      competence: query.competence,
      branch,
      startDate: query.startDate,
      endDate: query.endDate,
    }),
  );
}

function getCachedIndicators(
  query: ReadCacheQuery,
  branch?: string,
): IndicatorViewItem[] | null {
  const cached = getStrategicIndicatorsCachedValue<IndicatorsReadCache>(
    buildStrategicIndicatorsCacheKey("indicators", {
      competence: query.competence,
      branch,
      startDate: query.startDate,
      endDate: query.endDate,
    }),
  );

  return cached?.items ?? null;
}

function getCachedExecutive(
  query: ReadCacheQuery,
  branch?: string,
): ExecutiveDashboardViewData | null {
  return getStrategicIndicatorsCachedValue<ExecutiveDashboardViewData>(
    buildStrategicIndicatorsCacheKey("executive-summary", {
      competence: query.competence,
      branch,
      startDate: query.startDate,
      endDate: query.endDate,
    }),
  );
}

/** Monta a árvore a partir do cache compartilhado das rotas GET (sem esperar o bundle da árvore). */
export function tryBuildDepartmentTreeFromReadCache({
  viewMode,
  branch,
  scopes,
  query,
}: {
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  scopes: DepartmentTreeScopeConfig[];
  query: ReadCacheQuery;
}): DepartmentTreeModel | null {
  const executiveBranch =
    viewMode === "branch" && branch.trim() ? branch.trim() : undefined;

  const executive = getCachedExecutive(query, executiveBranch);
  if (!executive) {
    return null;
  }

  const scopePayloads: DepartmentTreeScopePayload[] = [];

  for (const scope of scopes) {
    const departments = getCachedDepartments(query, scope.branch);
    const indicators = getCachedIndicators(query, scope.branch);

    if (!departments || !indicators) {
      return null;
    }

    scopePayloads.push({
      scope,
      departments,
      indicators,
    });
  }

  return buildDepartmentTreeModel({
    competence: executive.competence,
    igd: executive.igd,
    igdExact: executive.igdExact,
    classification: executive.classification,
    scopePayloads,
  });
}
