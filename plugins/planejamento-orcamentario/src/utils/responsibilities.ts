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
  return `${params.userName} será ${role} por CAPEX e Pessoal do centro de custo ${params.costCenterLabel} no exercício ${params.exerciseYear}.`;
}

export function unitCatalogLabel(
  units: Array<{ code: string; name: string }>,
  code?: string | null,
): string {
  if (!code) return "—";
  const found = units.find((u) => u.code === code);
  return found ? `${found.code} — ${found.name}` : code;
}

export function areaCatalogLabel(
  areas: Array<{ code: string; name: string }>,
  code?: string | null,
): string {
  if (!code) return "—";
  const found = areas.find((a) => a.code === code);
  return found ? `${found.code} — ${found.name}` : code;
}

/** Chave lógica do vínculo: exercício + usuário + filial + centro (CAPEX e Pessoal juntos). */
export function responsibilityPairKey(row: {
  exercise_id: string;
  user_sub: string;
  unit_id: string;
  cost_center_id: string;
}): string {
  return [
    row.exercise_id,
    row.user_sub,
    row.unit_id,
    row.cost_center_id,
  ].join("::");
}

export type ResponsibilityPair = {
  key: string;
  exercise_id: string;
  user_sub: string;
  unit_id: string;
  cost_center_id: string;
  area_id: string | null;
  branch: string | null;
  responsibility_type: ResponsibilityType | string;
  valid_from?: string | null;
  valid_until?: string | null;
  is_active: boolean;
  user_name_snapshot?: string | null;
  user_email_snapshot?: string | null;
  updated_at?: string | null;
  created_at?: string | null;
  capex: BudgetResponsibility | null;
  personnel: BudgetResponsibility | null;
  rows: BudgetResponsibility[];
};

/**
 * Agrupa linhas CAPEX/Pessoal do mesmo usuário+exercício+filial+CC em um único vínculo.
 */
export function mergeResponsibilityPairs(
  items: BudgetResponsibility[],
): ResponsibilityPair[] {
  const map = new Map<string, ResponsibilityPair>();

  for (const row of items) {
    const key = responsibilityPairKey(row);
    const current =
      map.get(key) ??
      ({
        key,
        exercise_id: row.exercise_id,
        user_sub: row.user_sub,
        unit_id: row.unit_id,
        cost_center_id: row.cost_center_id,
        area_id: row.area_id ?? null,
        branch: row.branch ?? row.unit_id ?? null,
        responsibility_type: row.responsibility_type,
        valid_from: row.valid_from,
        valid_until: row.valid_until,
        is_active: false,
        user_name_snapshot: row.user_name_snapshot,
        user_email_snapshot: row.user_email_snapshot,
        updated_at: row.updated_at,
        created_at: row.created_at,
        capex: null,
        personnel: null,
        rows: [],
      } satisfies ResponsibilityPair);

    if (row.module === "personnel") {
      current.personnel = row;
    } else {
      current.capex = row;
    }
    current.rows.push(row);
    current.area_id = current.area_id ?? row.area_id ?? null;
    current.branch = current.branch ?? row.branch ?? row.unit_id ?? null;
    current.user_name_snapshot =
      current.user_name_snapshot || row.user_name_snapshot;
    current.user_email_snapshot =
      current.user_email_snapshot || row.user_email_snapshot;

    if (row.is_active) {
      current.is_active = true;
      current.responsibility_type = row.responsibility_type;
      current.valid_from = row.valid_from;
      current.valid_until = row.valid_until;
    }

    const rowUpdated = row.updated_at || row.created_at;
    const curUpdated = current.updated_at || current.created_at;
    if (rowUpdated && (!curUpdated || rowUpdated > curUpdated)) {
      current.updated_at = row.updated_at;
      current.created_at = row.created_at;
    }

    map.set(key, current);
  }

  return Array.from(map.values()).sort((a, b) => {
    const byUser = displayUser(a).localeCompare(displayUser(b), "pt-BR");
    if (byUser !== 0) return byUser;
    const byUnit = a.unit_id.localeCompare(b.unit_id);
    if (byUnit !== 0) return byUnit;
    return a.cost_center_id.localeCompare(b.cost_center_id);
  });
}

export function displayUser(
  row: Pick<BudgetResponsibility, "user_name_snapshot" | "user_sub"> | ResponsibilityPair,
): string {
  return (row.user_name_snapshot || row.user_sub || "—").trim();
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
