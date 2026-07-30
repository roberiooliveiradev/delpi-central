import { useEffect, useState } from "react";

export const CEC_CORPORATE_UNIT = "00";

export function useCecRouterPath(pathnameFromHost?: string) {
  const [pathname, setPathname] = useState(
    () => pathnameFromHost || window.location.pathname,
  );

  useEffect(() => {
    if (pathnameFromHost) {
      setPathname(pathnameFromHost);
      return;
    }
    const onPop = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [pathnameFromHost]);

  return pathname;
}

export type CecRoute =
  | { kind: "home" }
  | { kind: "list"; unitCode: string }
  | { kind: "members"; unitCode: string }
  | { kind: "new"; unitCode: string }
  | { kind: "detail"; unitCode: string; minuteId: string }
  | { kind: "edit"; unitCode: string; minuteId: string }
  | { kind: "sign"; unitCode: string; minuteId: string }
  | { kind: "pending" }
  | { kind: "mySignature" }
  | { kind: "unknown" };

/** Paths canônicos do comitê único (sem filial). */
export function parseCecRoute(pathname: string): CecRoute {
  const path = pathname.replace(/\/+$/, "") || "/";
  const base = "/apps/comite-etica-conduta";

  if (path === base || path === `${base}/atas`) {
    return { kind: "list", unitCode: CEC_CORPORATE_UNIT };
  }
  if (path === `${base}/pending` || path === `${base}/atas/pending`) {
    return { kind: "pending" };
  }
  if (
    path === `${base}/minha-assinatura` ||
    path === `${base}/my-signature`
  ) {
    return { kind: "mySignature" };
  }
  if (path === `${base}/membros` || path === `${base}/members`) {
    return { kind: "members", unitCode: CEC_CORPORATE_UNIT };
  }
  if (path === `${base}/atas/new` || path === `${base}/minutes/new`) {
    return { kind: "new", unitCode: CEC_CORPORATE_UNIT };
  }

  const ataMatch = path.match(
    new RegExp(`^${base}/(?:atas|minutes)/([^/]+)(?:/(edit|sign))?$`),
  );
  if (ataMatch) {
    const minuteId = ataMatch[1];
    const action = ataMatch[2];
    if (minuteId === "new") return { kind: "new", unitCode: CEC_CORPORATE_UNIT };
    if (action === "edit") {
      return { kind: "edit", unitCode: CEC_CORPORATE_UNIT, minuteId };
    }
    if (action === "sign") {
      return { kind: "sign", unitCode: CEC_CORPORATE_UNIT, minuteId };
    }
    return { kind: "detail", unitCode: CEC_CORPORATE_UNIT, minuteId };
  }

  // Compat com deep links antigos estilo CIPA (filial-*)
  const legacy = path.match(
    /\/apps\/comite-etica-conduta\/filial-(?:01|02)(?:\/minutes\/([^/]+))?(?:\/(edit|sign))?$/,
  );
  if (legacy) {
    const minuteId = legacy[1];
    const action = legacy[2];
    if (!minuteId) return { kind: "list", unitCode: CEC_CORPORATE_UNIT };
    if (minuteId === "new") return { kind: "new", unitCode: CEC_CORPORATE_UNIT };
    if (action === "edit") {
      return { kind: "edit", unitCode: CEC_CORPORATE_UNIT, minuteId };
    }
    if (action === "sign") {
      return { kind: "sign", unitCode: CEC_CORPORATE_UNIT, minuteId };
    }
    return { kind: "detail", unitCode: CEC_CORPORATE_UNIT, minuteId };
  }

  if (path.startsWith(base)) {
    return { kind: "list", unitCode: CEC_CORPORATE_UNIT };
  }
  return { kind: "unknown" };
}

export function navigateCec(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function cecAtaPath(minuteId: string, action?: "edit" | "sign") {
  const base = `/apps/comite-etica-conduta/atas/${minuteId}`;
  return action ? `${base}/${action}` : base;
}
