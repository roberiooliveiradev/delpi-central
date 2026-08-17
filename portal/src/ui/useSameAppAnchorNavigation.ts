import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { resolveSameAppSpaNavigation } from "../utils/sameAppAnchorNavigation";

function normalizeBasePath(basePath: string): string {
  const withSlash = basePath.startsWith("/") ? basePath : `/${basePath}`;
  return withSlash.replace(/\/+$/, "") || "/";
}

/**
 * Intercepta <a href> internos do app atual e navega via React Router,
 * evitando reload completo + tela de “abrindo app”.
 */
export function useSameAppAnchorNavigation(appBasePath: string | null | undefined) {
  const navigate = useNavigate();

  useEffect(() => {
    if (!appBasePath) return;
    const base = normalizeBasePath(appBasePath);

    const onClick = (event: MouseEvent) => {
      const raw = event.target;
      if (!(raw instanceof Element)) return;
      const anchor = raw.closest("a[href]");
      if (!(anchor instanceof HTMLAnchorElement)) return;

      const next = resolveSameAppSpaNavigation(event, anchor, {
        appBasePath: base,
        currentOrigin: window.location.origin,
        currentPathname: window.location.pathname,
        currentSearch: window.location.search,
        currentHash: window.location.hash,
      });
      if (next == null) return;

      event.preventDefault();
      const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
      if (next === current) return;
      navigate(next);
    };

    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, [appBasePath, navigate]);
}
