import { useEffect, useState } from "react";

export function useCipaRouterPath(pathnameFromHost?: string) {
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

export type CipaRoute =
  | { kind: "home" }
  | { kind: "list"; unitCode: "01" | "02" }
  | { kind: "members"; unitCode: "01" | "02" }
  | { kind: "new"; unitCode: "01" | "02" }
  | { kind: "detail"; unitCode: "01" | "02"; minuteId: string }
  | { kind: "edit"; unitCode: "01" | "02"; minuteId: string }
  | { kind: "sign"; unitCode: "01" | "02"; minuteId: string }
  | { kind: "pending" }
  | { kind: "mySignature" }
  | { kind: "unknown" };

export function parseCipaRoute(pathname: string): CipaRoute {
  const path = pathname.replace(/\/+$/, "") || "/";
  if (path === "/apps/cipa") {
    return { kind: "home" };
  }
  if (path.endsWith("/pending") || path.includes("/cipa/pending")) {
    return { kind: "pending" };
  }
  if (path.endsWith("/my-signature") || path.includes("/cipa/my-signature")) {
    return { kind: "mySignature" };
  }
  const membersMatch = path.match(/\/apps\/cipa\/filial-(01|02)\/members$/);
  if (membersMatch) {
    return { kind: "members", unitCode: membersMatch[1] as "01" | "02" };
  }
  const match = path.match(
    /\/apps\/cipa\/filial-(01|02)(?:\/minutes\/([^/]+))?(?:\/(edit|sign))?$/,
  );
  if (!match) {
    if (path.includes("/filial-01")) return { kind: "list", unitCode: "01" };
    if (path.includes("/filial-02")) return { kind: "list", unitCode: "02" };
    return { kind: "unknown" };
  }
  const unitCode = match[1] as "01" | "02";
  const minuteId = match[2];
  const action = match[3];
  if (!minuteId) return { kind: "list", unitCode };
  if (minuteId === "new") return { kind: "new", unitCode };
  if (action === "edit") return { kind: "edit", unitCode, minuteId };
  if (action === "sign") return { kind: "sign", unitCode, minuteId };
  return { kind: "detail", unitCode, minuteId };
}

export function navigateCipa(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
