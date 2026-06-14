const ADMIN_SUFFIX = "/admin";

export type CulturaDelpiRoute = "public" | "admin";

function resolvePathname(pathname?: string): string {
  if (typeof window !== "undefined" && window.location.pathname) {
    return window.location.pathname.replace(/\/+$/, "");
  }

  return (pathname ?? "").replace(/\/+$/, "");
}

export function resolveCulturaDelpiRoute(pathname?: string): CulturaDelpiRoute {
  const path = resolvePathname(pathname);

  if (path.endsWith(ADMIN_SUFFIX)) {
    return "admin";
  }

  return "public";
}
