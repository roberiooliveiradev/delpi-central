import {
  buildCustomerDetailPath,
  buildPluginPath,
  normalizePathname,
  type PluginView,
} from "./pluginRoutes";

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
  view: Exclude<PluginView, "customer_detail" | "not_found">,
  options?: { basePath?: string; search?: string },
): void {
  const target = buildPluginPath(view, options?.basePath, options?.search);
  navigatePluginPath(target);
}

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
