import type { AppItem, RouteItem } from "../data/coreApi";

export function normalizePathname(pathname: string): string {
  const value = pathname.trim() || "/";
  return value.replace(/\/+$/, "") || "/";
}

/** Rota do manifest com maior prefixo que casa com o pathname (suporta rotas aninhadas do MFE). */
export function resolveMatchingRoute(
  routes: RouteItem[] | undefined,
  pathname: string,
): RouteItem | null {
  if (!routes?.length) return null;

  const normalized = normalizePathname(pathname);
  const matches = routes.filter((route) => {
    const routePath = normalizePathname(route.path);
    return normalized === routePath || normalized.startsWith(`${routePath}/`);
  });

  if (!matches.length) return null;

  return matches.sort((a, b) => b.path.length - a.path.length)[0];
}

export function isExternalHttpUrl(value: string | undefined): boolean {
  if (!value) return false;
  return /^https?:\/\//i.test(value.trim());
}

export function isFederationRemoteEntry(value: string | undefined): boolean {
  if (!value) return false;
  return value.includes("remoteEntry.js");
}

/** Entry usada para carregar iframe / external. */
export function resolveHostedEntry(app: AppItem, route: RouteItem | null): string | undefined {
  const routeEntry = route?.entry?.trim();
  const appEntry = app.entryUrl?.trim();

  if (app.renderMode === "federated") {
    return appEntry || undefined;
  }

  return routeEntry || appEntry || undefined;
}

/** Entry do Module Federation — sempre a do app, nunca link alternativo de rota. */
export function resolveFederationEntry(app: AppItem | null): string | undefined {
  if (!app || app.renderMode !== "federated") return undefined;
  return app.entryUrl?.trim() || undefined;
}

/**
 * Link alternativo declarado em routes[].entry (ex.: Google Apps Script).
 * Em federated não substitui o remoteEntry; pode ser repassado ao MFE ou exibido na UI.
 */
export function resolveRouteAlternateUrl(
  app: AppItem | null,
  route: RouteItem | null,
): string | undefined {
  if (!app || !route) return undefined;

  const routeEntry = route.entry?.trim();
  if (!routeEntry || !isExternalHttpUrl(routeEntry)) return undefined;

  if (app.renderMode === "federated") {
    return routeEntry;
  }

  return undefined;
}
