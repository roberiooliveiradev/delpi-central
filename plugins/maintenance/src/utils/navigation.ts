import { LEGACY_CONFIGURACAO_ROUTE, LEGACY_RELATORIO_ROUTE } from "../constants/routes";
import { normalizeMaintenancePath } from "./routeParser";

const LEGACY_ROUTE_MAP: Record<string, string> = {
  [LEGACY_RELATORIO_ROUTE]: "/apps/maintenance/mini-aplicadores/relatorio",
  [LEGACY_CONFIGURACAO_ROUTE]: "/apps/maintenance/mini-aplicadores/configuracao",
};

export function navigateMaintenance(path: string) {
  const normalized = normalizeMaintenancePath(path);
  const target = LEGACY_ROUTE_MAP[normalized] ?? normalized;

  if (typeof window === "undefined") return;

  if (window.location.pathname === target) {
    return;
  }

  window.history.pushState(null, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
