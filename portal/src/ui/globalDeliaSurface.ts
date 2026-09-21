import type { AppItem, MeResponse, RouteItem } from "../data/coreApi";
import {
  resolveMatchingRoute,
  resolveRouteAlternateUrl,
  toFederatedAppRouteProps,
} from "./appHostEntry";
import type { FederatedHostProps } from "./federatedRemoteHost";

/** Registered Core application id — composition hook, not a second catalog. */
export const DELIA_APP_ID = "delia";

/** Same Module Federation expose used by full-page AppHost. */
export const DELIA_EXPOSED_MODULE = "./App";

export function normalizeAppBasePath(basePath: string) {
  const normalized = basePath.startsWith("/") ? basePath : `/${basePath}`;
  return normalized.replace(/\/+$/, "") || "/";
}

/**
 * Visibility comes only from Core-filtered `/me/apps`.
 * Do not consult permissions, roles, groups, or isSuperadmin.
 */
export function findAuthorizedDeliaApp(apps: AppItem[] | undefined): AppItem | null {
  if (!apps?.length) return null;
  return apps.find((app) => app.id === DELIA_APP_ID) ?? null;
}

export function resolveDeliaExposedModule(app: AppItem | null): string {
  if (!app) return DELIA_EXPOSED_MODULE;
  const exposed = (app as AppItem & { exposedModule?: string }).exposedModule?.trim();
  return exposed || DELIA_EXPOSED_MODULE;
}

export function isDeliaFullPagePath(pathname: string, basePath?: string): boolean {
  const base = normalizeAppBasePath(basePath || "/apps/delia");
  const path = normalizeAppBasePath(pathname);
  return path === base || path.startsWith(`${base}/`);
}

export function shouldRenderGlobalDeliaLauncher(options: {
  apps: AppItem[] | undefined;
  pathname: string;
}): boolean {
  const app = findAuthorizedDeliaApp(options.apps);
  if (!app) return false;
  return !isDeliaFullPagePath(options.pathname, app.basePath);
}

export function shouldKeepGlobalDeliaPanelOpen(options: {
  apps: AppItem[] | undefined;
  pathname: string;
  requestedOpen: boolean;
}): boolean {
  if (!options.requestedOpen) return false;
  return shouldRenderGlobalDeliaLauncher(options);
}

export type GlobalDeliaHostInput = {
  app: AppItem;
  pathname: string;
  search: string;
  getAccessToken: () => string | undefined;
  user?: Pick<MeResponse, "permissions" | "is_superadmin"> | null;
};

/**
 * Frozen host props only. Pathname/search are the current browser location.
 * routeLabel / alternateEntry stay unset unless the current path is a DÉLIA route.
 * Does not infer OP, machine, product, operation, posto, or business filters.
 */
export function buildGlobalDeliaHostProps(input: GlobalDeliaHostInput): FederatedHostProps {
  const deliaRoute: RouteItem | null = isDeliaFullPagePath(input.pathname, input.app.basePath)
    ? resolveMatchingRoute(input.app.routes, input.pathname)
    : null;

  return {
    getAccessToken: input.getAccessToken,
    basePath: input.app.basePath,
    pathname: input.pathname,
    search: input.search,
    alternateEntry: resolveRouteAlternateUrl(input.app, deliaRoute),
    appRoutes: toFederatedAppRouteProps(input.app.routes),
    routeLabel: deliaRoute?.label,
    permissions: input.user?.permissions,
    isSuperadmin: input.user?.is_superadmin,
  };
}
