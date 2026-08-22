import type { TravelAccess, UnitAccess } from "../api/travelExpensesApi";

export type UnitCode = "01" | "02";

const UNIT_LABELS: Record<UnitCode, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

export function emptyAccess(): TravelAccess {
  return { admin: false, canView: false, canWrite: false, canManage: false, units: [] };
}

export function buildAccessFromPermissions(
  permissions: string[] | undefined,
  isSuperadmin?: boolean,
): TravelAccess {
  const set = new Set(permissions || []);
  const admin = Boolean(isSuperadmin) || set.has("travel-expenses.admin");
  const canWrite = admin || set.has("travel-expenses.write") || set.has("travel-expenses.manage");
  const canView = admin || canWrite || set.has("travel-expenses.view");
  const canManage = admin || set.has("travel-expenses.manage");
  const units: UnitAccess[] = (["01", "02"] as UnitCode[])
    .filter((id) => admin || set.has(`travel-expenses.unit.filial-${id}`))
    .map((id) => ({
      id,
      label: UNIT_LABELS[id],
      view: canView || admin,
      write: canWrite,
      manage: canManage,
    }));
  return { admin, canView, canWrite, canManage, units };
}

export function writableUnits(access: TravelAccess) {
  return access.units.filter((unit) => unit.write);
}

export function readableUnits(access: TravelAccess) {
  return access.units.filter((unit) => unit.view);
}
