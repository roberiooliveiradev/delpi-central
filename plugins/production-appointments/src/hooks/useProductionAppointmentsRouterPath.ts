import { useEffect, useState } from "react";

function readPathname(): string {
  if (typeof window === "undefined") return "";
  return window.location.pathname;
}

/**
 * Prefere navegação interna (pushState) quando o browser já está em rota
 * mais específica que o pathname do host (ex.: detalhe da OP).
 */
export function useProductionAppointmentsRouterPath(pathnameFromHost?: string): string {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost ?? readPathname(),
  );

  useEffect(() => {
    if (!pathnameFromHost) return;
    // Só sincroniza do host quando ele bate com o browser — evita o portal
    // resetar `/…/op/:id` de volta para `/…/sc` a cada render.
    if (pathnameFromHost === readPathname()) {
      setPathname(pathnameFromHost);
    }
  }, [pathnameFromHost]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const syncFromBrowser = () => {
      setPathname(readPathname());
    };

    window.addEventListener("popstate", syncFromBrowser);
    return () => window.removeEventListener("popstate", syncFromBrowser);
  }, []);

  return pathname;
}
