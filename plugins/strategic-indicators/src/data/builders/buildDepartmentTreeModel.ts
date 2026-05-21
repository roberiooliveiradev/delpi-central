import type { DepartmentOverviewViewItem } from "../types/departments";
import type { IndicatorViewItem } from "../types/indicators";
import type {
  DepartmentTreeColumn,
  DepartmentTreeDepartmentNode,
  DepartmentTreeModel,
  DepartmentTreeScopeConfig,
} from "../types/departmentTree";

export type DepartmentTreeScopePayload = {
  scope: DepartmentTreeScopeConfig;
  departments: DepartmentOverviewViewItem[];
  indicators: IndicatorViewItem[];
};

function averageScore(departments: DepartmentOverviewViewItem[]): number | null {
  if (!departments.length) return null;
  const total = departments.reduce((sum, item) => sum + item.score, 0);
  return Math.round((total / departments.length) * 10) / 10;
}

function buildDepartmentNodes(
  departments: DepartmentOverviewViewItem[],
  indicators: IndicatorViewItem[],
  departmentOrder: string[],
): DepartmentTreeDepartmentNode[] {
  const byDepartment = new Map<string, IndicatorViewItem[]>();

  for (const indicator of indicators) {
    const list = byDepartment.get(indicator.departmentId) ?? [];
    list.push(indicator);
    byDepartment.set(indicator.departmentId, list);
  }

  for (const list of byDepartment.values()) {
    list.sort((a, b) => b.weightPct - a.weightPct);
  }

  const departmentById = new Map(departments.map((item) => [item.id, item]));
  const orderedIds = [
    ...departmentOrder.filter((id) => departmentById.has(id)),
    ...departments
      .map((item) => item.id)
      .filter((id) => !departmentOrder.includes(id)),
  ];

  return orderedIds
    .map((id) => departmentById.get(id))
    .filter((item): item is DepartmentOverviewViewItem => Boolean(item))
    .map((department) => ({
      department,
      series: [],
      indicators: (byDepartment.get(department.id) ?? []).map((indicator) => ({
        indicator,
        series: [],
      })),
    }));
}

export function buildDepartmentTreeModel({
  competence,
  igd,
  igdExact,
  classification,
  scopePayloads,
}: {
  competence: string;
  igd: number | null;
  igdExact: number | null;
  classification: string | null;
  scopePayloads: DepartmentTreeScopePayload[];
}): DepartmentTreeModel {
  const consolidatedPayload = scopePayloads.find(
    (item) => item.scope.key === "consolidated",
  );
  const departmentOrder = (
    consolidatedPayload?.departments.length
      ? consolidatedPayload.departments
      : scopePayloads[0]?.departments ?? []
  ).map((item) => item.id);

  const columns: DepartmentTreeColumn[] = scopePayloads.map((payload) => {
    const departmentNodes = buildDepartmentNodes(
      payload.departments,
      payload.indicators,
      departmentOrder,
    );

    return {
      scope: payload.scope,
      departments: departmentNodes,
      averageScore: averageScore(payload.departments),
      hasData: departmentNodes.length > 0,
    };
  });

  return {
    competence,
    igd,
    igdExact,
    classification,
    igdSeries: [],
    columns,
    departmentOrder,
  };
}
