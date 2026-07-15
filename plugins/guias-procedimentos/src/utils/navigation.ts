import { normalizeGuiasProcedimentosPath } from "./route";

export function navigateGuiasProcedimentos(path: string) {
  const target = normalizeGuiasProcedimentosPath(path);

  if (typeof window === "undefined") return;

  if (window.location.pathname === target) {
    return;
  }

  window.history.pushState(null, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
