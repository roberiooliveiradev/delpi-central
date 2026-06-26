import { APP_BASE } from "../constants/actionPlans";

function normalizePacPath(path: string): string {
  const trimmed = path.trim();
  if (!trimmed) return APP_BASE;
  if (trimmed.startsWith(APP_BASE)) return trimmed.replace(/\/+$/, "");
  if (trimmed.startsWith("/")) return `${APP_BASE}${trimmed}`.replace(/\/+$/, "");
  return `${APP_BASE}/${trimmed}`.replace(/\/+$/, "");
}

export function navigatePac(path: string): void {
  if (typeof window === "undefined") return;

  const target = normalizePacPath(path);
  if (window.location.pathname === target) {
    return;
  }

  window.history.pushState(null, "", target);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
