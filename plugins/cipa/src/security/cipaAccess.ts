export type CipaUnitCode = "01" | "02";

export type CipaUnitAccess = {
  id: CipaUnitCode;
  label: string;
  view: boolean;
  manage: boolean;
  sign: boolean;
  sipat_view?: boolean;
  sipat_manage?: boolean;
};

export type CipaAccess = {
  admin: boolean;
  can_view: boolean;
  can_manage: boolean;
  can_sign: boolean;
  can_sipat_view?: boolean;
  can_sipat_manage?: boolean;
  units: CipaUnitAccess[];
};

export function unitAccess(
  access: CipaAccess | null | undefined,
  unitCode: string,
): CipaUnitAccess | undefined {
  return access?.units.find((unit) => unit.id === unitCode);
}

export function canUnit(
  access: CipaAccess | null | undefined,
  unitCode: string,
  action: "view" | "manage" | "sign" | "sipat_view" | "sipat_manage",
): boolean {
  const unit = unitAccess(access, unitCode);
  if (!unit) return false;
  if (action === "sipat_view") {
    return Boolean(unit.sipat_view || unit.sipat_manage || unit.manage);
  }
  if (action === "sipat_manage") {
    return Boolean(unit.sipat_manage || unit.manage);
  }
  return Boolean(unit[action]);
}

export function readableUnits(access: CipaAccess | null | undefined): CipaUnitAccess[] {
  return (access?.units ?? []).filter(
    (unit) => unit.view || unit.sipat_view || unit.sipat_manage,
  );
}
