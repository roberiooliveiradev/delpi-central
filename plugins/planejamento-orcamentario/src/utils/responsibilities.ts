import type {
  BudgetExercise,
  BudgetResponsibility,
  OrgCatalog,
  OrgCostCenter,
  ResponsibilityType,
} from "../types/budgetPlanning";
import {
  costCenterBranch,
  costCenterCode,
  formatCostCenterLabel,
  normalizeBranchCode,
} from "./orgCostCenters";

export function responsibilityTypeLabel(type: ResponsibilityType | string): string {
  if (type === "owner") return "Responsável";
  if (type === "collaborator") return "Colaborador";
  return type;
}

export function formatDateBr(value?: string | null): string {
  if (!value) return "—";
  const raw = value.length >= 10 ? value.slice(0, 10) : value;
  const [y, m, d] = raw.split("-");
  if (!y || !m || !d) return value;
  return `${d}/${m}/${y}`;
}

export function formatValidity(
  validFrom?: string | null,
  validUntil?: string | null,
): string {
  if (!validFrom && !validUntil) return "Sem limite";
  return `${formatDateBr(validFrom)} → ${formatDateBr(validUntil)}`;
}

export function exerciseLabel(
  exercises: BudgetExercise[],
  exerciseId: string,
): string {
  const found = exercises.find((e) => e.id === exerciseId);
  if (!found) return exerciseId.slice(0, 8);
  return `${found.year} — ${found.name}`;
}

export function catalogLabel(
  items: Array<{ code: string; name: string; branch?: string | null; unit_code?: string | null }>,
  code?: string | null,
  branch?: string | null,
): string {
  if (!code) return "—";
  const branchNorm = normalizeBranchCode(branch);
  const found = items.find((i) => {
    if (i.code !== code) return false;
    if (!branchNorm) return true;
    const itemBranch = normalizeBranchCode(i.branch) || normalizeBranchCode(i.unit_code);
    return !itemBranch || itemBranch === branchNorm;
  });
  if (!found) {
    return branchNorm ? formatCostCenterLabel({ branch: branchNorm, code }) : code;
  }
  return formatCostCenterLabel({
    branch: found.branch ?? found.unit_code ?? branchNorm,
    code: found.code,
    name: found.name,
  });
}

export function findOrgCostCenter(
  catalog: OrgCatalog | null,
  code: string,
  branch?: string | null,
): OrgCostCenter | undefined {
  const branchNorm = normalizeBranchCode(branch);
  return (catalog?.cost_centers ?? []).find((cc) => {
    if (costCenterCode(cc) !== code) return false;
    if (!branchNorm) return true;
    return costCenterBranch(cc) === branchNorm;
  });
}

export function buildCreateSummary(params: {
  userName: string;
  costCenterLabel: string;
  exerciseYear: number | string;
  type: ResponsibilityType;
}): string {
  const role =
    params.type === "owner"
      ? "responsável"
      : "colaborador(a)";
  return `${params.userName} será ${role} pelo CAPEX do centro de custo ${params.costCenterLabel} no exercício ${params.exerciseYear}.`;
}

export function validateValidityRange(
  validFrom?: string | null,
  validUntil?: string | null,
): string | null {
  if (validFrom && validUntil && validUntil < validFrom) {
    return "A data final da vigência não pode ser anterior à inicial.";
  }
  return null;
}

export function filterAreasForUnit(catalog: OrgCatalog | null, unitId: string) {
  return (catalog?.areas ?? []).filter(
    (a) => !a.unit_code || a.unit_code === unitId,
  );
}

export function filterCostCenters(
  catalog: OrgCatalog | null,
  unitId: string,
  areaId: string,
) {
  const branch = normalizeBranchCode(unitId);
  return (catalog?.cost_centers ?? []).filter((cc) => {
    const ccBranch = costCenterBranch(cc);
    if (branch && ccBranch && ccBranch !== branch) return false;
    if (!branch && cc.unit_code && unitId && cc.unit_code !== unitId) return false;
    if (areaId && cc.area_code && cc.area_code !== areaId) return false;
    if (cc.active === false) return false;
    return true;
  });
}

export function displayUser(row: BudgetResponsibility): string {
  return (row.user_name_snapshot || row.user_sub || "—").trim();
}
