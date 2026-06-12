import { normalizeMaintenancePath } from "./routeParser";

export function navigateMaintenance(path: string) {
  const target = normalizeMaintenancePath(path);

  if (typeof window === "undefined") return;

  if (window.location.pathname === target) {
    return;
  }

  window.history.pushState(null, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
