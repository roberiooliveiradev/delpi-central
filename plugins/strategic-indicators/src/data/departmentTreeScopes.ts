import type { StrategicIndicatorsViewMode } from "../ui/shared/strategicIndicatorsFilters";
import type {
  DepartmentTreeColumn,
  DepartmentTreeScopeConfig,
  DepartmentTreeScopeKey,
} from "./types/departmentTree";

const BRANCH_SCOPE_KEYS = new Set<DepartmentTreeScopeKey>(["01", "02"]);

export const DEPARTMENT_TREE_SCOPE_OPTIONS: ReadonlyArray<{
  value: DepartmentTreeScopeKey;
  label: string;
}> = [
  { value: "consolidated", label: "Consolidado" },
  { value: "01", label: "Filial 01" },
  { value: "02", label: "Filial 02" },
];

export function resolveActiveTreeScopeKey(
  viewMode: StrategicIndicatorsViewMode,
  branch: string,
): DepartmentTreeScopeKey {
  if (viewMode === "branch") {
    const trimmed = branch.trim();
    return trimmed === "02" ? "02" : "01";
  }

  return "consolidated";
}

export function applyTreeScopeSelection(scope: DepartmentTreeScopeKey): {
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
} {
  if (scope === "consolidated") {
    return { viewMode: "consolidated", branch: "01" };
  }

  return { viewMode: "branch", branch: scope };
}

export function pickActiveTreeColumn(
  columns: DepartmentTreeColumn[],
  activeScopeKey: DepartmentTreeScopeKey,
): DepartmentTreeColumn | null {
  return (
    columns.find((column) => column.scope.key === activeScopeKey) ??
    columns[0] ??
    null
  );
}

export function resolveDepartmentTreeScopes(
  viewMode: StrategicIndicatorsViewMode,
  branch: string,
): DepartmentTreeScopeConfig[] {
  if (viewMode === "branch" && branch.trim()) {
    const key = branch.trim() as DepartmentTreeScopeKey;
    return [
      {
        key: BRANCH_SCOPE_KEYS.has(key) ? key : "01",
        branch: branch.trim(),
        label: `Filial ${branch.trim()}`,
      },
    ];
  }

  return [{ key: "consolidated", branch: undefined, label: "Consolidado" }];
}
