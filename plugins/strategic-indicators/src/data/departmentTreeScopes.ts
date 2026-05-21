import type { StrategicIndicatorsViewMode } from "../ui/shared/strategicIndicatorsFilters";
import type { DepartmentTreeScopeConfig, DepartmentTreeScopeKey } from "./types/departmentTree";

const BRANCH_SCOPE_KEYS = new Set<DepartmentTreeScopeKey>(["01", "02"]);

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
