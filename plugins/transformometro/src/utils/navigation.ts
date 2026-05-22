import { normalizeTransformometroPath } from "./routeParser";

export function navigateTransformometro(path: string) {
  const target = normalizeTransformometroPath(path);

  if (typeof window === "undefined") return;

  if (window.location.pathname === target) {
    return;
  }

  window.history.pushState(null, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
