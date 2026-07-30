import type { ComiteEticaAccess, ComiteEticaUnitCode } from "./cecAccess";

const VIEW = "comite-etica-conduta.view";
const MANAGE = "comite-etica-conduta.manage";
const SIGN = "comite-etica-conduta.sign";

function has(codes: string[], code: string): boolean {
  return codes.includes(code);
}

export function buildComiteEticaAccessFromPermissions(
  permissionCodes: string[],
  isSuperadmin = false,
): ComiteEticaAccess {
  const codes = permissionCodes ?? [];
  const admin = isSuperadmin;
  const can_view = admin || has(codes, VIEW) || has(codes, MANAGE);
  const can_manage = admin || has(codes, MANAGE);
  const can_sign = admin || has(codes, SIGN) || can_manage;

  const unit: ComiteEticaUnitCode = "00";
  return {
    admin,
    can_view,
    can_manage,
    can_sign,
    units: can_view
      ? [
          {
            id: unit,
            label: "Comitê de Ética e Conduta",
            view: can_view,
            manage: can_manage,
            sign: can_sign,
          },
        ]
      : [],
  };
}
