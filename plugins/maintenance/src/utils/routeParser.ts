import { MAINTENANCE_ROUTES } from "../constants/routes";

export type MaintenanceView =
  | "home"
  | "mini-aplicadores"
  | "mini-aplicador"
  | "relatorio"
  | "configuracao";

export type ParsedMaintenanceRoute = {
  view: MaintenanceView;
  codigoFerramenta?: string;
};

export function normalizeMaintenancePath(pathname: string): string {
  if (!pathname) return MAINTENANCE_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseMaintenancePath(pathname: string): ParsedMaintenanceRoute {
  const path = normalizeMaintenancePath(pathname);

  const detailMatch = path.match(/^\/apps\/maintenance\/mini-aplicadores\/([^/]+)$/);
  if (detailMatch) {
    return { view: "mini-aplicador", codigoFerramenta: detailMatch[1] };
  }

  if (path === MAINTENANCE_ROUTES.miniAplicadores) {
    return { view: "mini-aplicadores" };
  }
  if (path === MAINTENANCE_ROUTES.relatorio) {
    return { view: "relatorio" };
  }
  if (path === MAINTENANCE_ROUTES.configuracao) {
    return { view: "configuracao" };
  }

  return { view: "home" };
}
