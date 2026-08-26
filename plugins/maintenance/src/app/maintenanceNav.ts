import { MAINTENANCE_ROUTES } from "../constants/routes";
import type { MaintenanceView } from "../utils/routeParser";
import { resolveMaintenanceHomePath } from "../utils/routeParser";

export type MaintenanceNavId =
  | "home"
  | "filiais"
  | "mini-aplicadores"
  | "programas-maquinas"
  | "manutencao-geral";

export function resolveMaintenanceNavId(view: MaintenanceView): MaintenanceNavId {
  switch (view) {
    case "filiais":
      return "filiais";
    case "mini-aplicadores":
    case "mini-aplicador":
    case "relatorio":
    case "configuracao":
      return "mini-aplicadores";
    case "programas-maquinas":
      return "programas-maquinas";
    case "manutencao-geral":
      return "manutencao-geral";
    default:
      return "home";
  }
}

export function resolveMaintenanceNavPath(
  navId: MaintenanceNavId,
  filialScope?: string,
): string {
  switch (navId) {
    case "home":
      return resolveMaintenanceHomePath(filialScope);
    case "filiais":
      return MAINTENANCE_ROUTES.filiais;
    case "mini-aplicadores":
      return MAINTENANCE_ROUTES.miniAplicadores;
    case "programas-maquinas":
      return MAINTENANCE_ROUTES.programasMaquinas;
    case "manutencao-geral":
      return MAINTENANCE_ROUTES.manutencaoGeral(filialScope ?? "01");
    default:
      return MAINTENANCE_ROUTES.home;
  }
}
