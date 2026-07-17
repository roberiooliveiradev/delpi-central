export type CipaUnitCode = "01" | "02";

export type CipaUnitAccess = {
  id: CipaUnitCode;
  label: string;
  view: boolean;
  manage: boolean;
  sign: boolean;
};

export type CipaAccess = {
  admin: boolean;
  can_view: boolean;
  can_manage: boolean;
  can_sign: boolean;
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
  action: "view" | "manage" | "sign",
): boolean {
  return Boolean(unitAccess(access, unitCode)?.[action]);
}

export function readableUnits(access: CipaAccess | null | undefined): CipaUnitAccess[] {
  return (access?.units ?? []).filter((unit) => unit.view);
}
