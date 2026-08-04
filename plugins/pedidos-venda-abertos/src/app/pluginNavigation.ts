import { buildCustomerDetailPath } from "../features/customers/utils/customerDetailPath.ts";
import {
  buildPluginPath,
  normalizePathname,
  type PluginView,
} from "./pluginRoutes.ts";

/**
 * Navegação interna no padrão do monorepo (propostas-comerciais):
 * pushState + popstate. O Portal também reenvia pathname via updateRoute.
 */
export function navigatePluginPath(target: string): void {
  if (typeof window === "undefined") return;

  const current = `${normalizePathname(window.location.pathname)}${window.location.search || ""}`;
  if (current === target) return;

  window.history.pushState(null, "", target);
  const popState =
    typeof PopStateEvent === "function"
      ? new PopStateEvent("popstate")
      : new Event("popstate");
  window.dispatchEvent(popState);
}

export function navigatePluginView(
  view: Extract<PluginView, "orders" | "customers" | "config">,
  options?: { basePath?: string; search?: string },
): void {
  const target = buildPluginPath(view, options?.basePath, options?.search);
  navigatePluginPath(target);
}

/**
 * Navega para o detalhe do cliente. Retorna false se a identidade for inválida.
 */
export function navigateCustomerDetail(
  codigo: string,
  loja: string,
  options?: { basePath?: string },
): boolean {
  const path = buildCustomerDetailPath(options?.basePath, codigo, loja);
  if (!path) return false;
  navigatePluginPath(path);
  return true;
}

export { buildCustomerDetailPath };
