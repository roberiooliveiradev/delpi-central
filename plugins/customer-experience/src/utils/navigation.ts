import { APP_BASE } from "../constants/routes";

function normalizeCxPath(path: string): string {
  const trimmed = path.trim();
  if (!trimmed) return APP_BASE;
  if (trimmed.startsWith(APP_BASE)) return trimmed.replace(/\/+$/, "");
  if (trimmed.startsWith("/")) return `${APP_BASE}${trimmed}`.replace(/\/+$/, "");
  return `${APP_BASE}/${trimmed}`.replace(/\/+$/, "");
}

/** Atualiza a URL do navegador e notifica o app (deep-link + botão voltar). */
export function navigateCx(path: string, options?: { replace?: boolean }): void {
  if (typeof window === "undefined") return;

  const target = normalizeCxPath(path);
  if (window.location.pathname === target) return;

  if (options?.replace) {
    window.history.replaceState(null, "", target);
  } else {
    window.history.pushState(null, "", target);
  }
  window.dispatchEvent(new PopStateEvent("popstate"));
}
