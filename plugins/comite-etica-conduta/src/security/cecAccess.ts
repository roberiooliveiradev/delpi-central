export type ComiteEticaUnitCode = "00" | "01" | "02";

export type ComiteEticaUnitAccess = {
  id: ComiteEticaUnitCode;
  label: string;
  view: boolean;
  manage: boolean;
  sign: boolean;
};

export type ComiteEticaAccess = {
  admin: boolean;
  can_view: boolean;
  can_manage: boolean;
  can_sign: boolean;
  units: ComiteEticaUnitAccess[];
};

export function canUnit(
  access: ComiteEticaAccess | null | undefined,
  unitCode: string,
  action: "view" | "manage" | "sign",
): boolean {
  if (!access) return false;
  if (access.admin) return true;
  if (action === "view" && access.can_view) return true;
  if (action === "manage" && access.can_manage) return true;
  if (action === "sign" && access.can_sign) return true;
  const unit = access.units.find((item) => item.id === unitCode);
  if (!unit) {
    // Comitê corporativo: permissões globais bastam.
    return false;
  }
  return Boolean(unit[action]);
}

export function readableUnits(
  access: ComiteEticaAccess | null | undefined,
): ComiteEticaUnitAccess[] {
  if (!access) return [];
  if (access.admin || access.can_view) {
    return [
      {
        id: "00",
        label: "Comitê de Ética e Conduta",
        view: true,
        manage: access.admin || access.can_manage,
        sign: access.admin || access.can_sign,
      },
    ];
  }
  return access.units.filter((unit) => unit.view || unit.manage || unit.sign);
}
