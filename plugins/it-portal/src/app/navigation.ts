import { useSyncExternalStore, type MouseEvent } from "react";

import { normalizePathname } from "./routes";

/** Navegação SPA dentro do host: pushState + popstate (o host observa a URL). */
export function navigateTo(target: string, options?: { replace?: boolean }): void {
  if (typeof window === "undefined") return;
  const current = `${normalizePathname(window.location.pathname)}${window.location.search || ""}`;
  if (current === target) return;
  if (options?.replace) {
    window.history.replaceState(null, "", target);
  } else {
    window.history.pushState(null, "", target);
  }
  window.dispatchEvent(new PopStateEvent("popstate"));
}

/** Handler de `<a href>` interno: navegação SPA no clique simples; Ctrl/middle-click mantêm o nativo. */
export function spaNavigate(href: string) {
  return (event: MouseEvent<HTMLAnchorElement>) => {
    if (event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    navigateTo(href);
  };
}

function subscribe(onChange: () => void) {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

/**
 * Pathname atual do browser. O host também repassa `pathname` em `updateRoute`,
 * o que re-renderiza o app e relê `window.location`.
 */
export function usePluginPathname(pathnameFromHost?: string): string {
  return useSyncExternalStore(
    subscribe,
    () => window.location.pathname,
    () => pathnameFromHost ?? "/",
  );
}
