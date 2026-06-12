import {
  LEGACY_CONFIGURACAO_ROUTE,
  LEGACY_RELATORIO_ROUTE,
  MAINTENANCE_ROUTES,
} from "../constants/routes";

export type MaintenanceView =
  | "home"
  | "mini-aplicadores"
  | "mini-aplicador"
  | "relatorio"
  | "configuracao";

export type ParsedMaintenanceRoute = {
  view: MaintenanceView;
  codigoFerramenta?: string;
  filialScope?: string;
};

const MINI_APP = MAINTENANCE_ROUTES.miniAplicadores;
const RESERVED_MINI_SEGMENTS = new Set(["relatorio", "configuracao"]);

export function normalizeMaintenancePath(pathname: string): string {
  if (!pathname) return MAINTENANCE_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseMaintenancePath(pathname: string): ParsedMaintenanceRoute {
  const path = normalizeMaintenancePath(pathname);

  const filialHomeMatch = path.match(/^\/apps\/maintenance\/filial-(01|02)$/);
  if (filialHomeMatch) {
    return { view: "home", filialScope: filialHomeMatch[1] };
  }

  if (path === MAINTENANCE_ROUTES.miniAplicadoresRelatorio || path === LEGACY_RELATORIO_ROUTE) {
    return { view: "relatorio" };
  }

  if (
    path === MAINTENANCE_ROUTES.miniAplicadoresConfiguracao ||
    path === LEGACY_CONFIGURACAO_ROUTE
  ) {
    return { view: "configuracao" };
  }

  const detailMatch = path.match(/^\/apps\/maintenance\/mini-aplicadores\/([^/]+)$/);
  if (detailMatch && !RESERVED_MINI_SEGMENTS.has(detailMatch[1])) {
    return { view: "mini-aplicador", codigoFerramenta: detailMatch[1] };
  }

  if (path === MINI_APP) {
    return { view: "mini-aplicadores" };
  }

  if (path === MAINTENANCE_ROUTES.home) {
    return { view: "home" };
  }

  return { view: "home" };
}

export function resolveMaintenanceHomePath(filialScope?: string): string {
  if (filialScope === "01" || filialScope === "02") {
    return MAINTENANCE_ROUTES.filialHome(filialScope);
  }
  return MAINTENANCE_ROUTES.home;
}
