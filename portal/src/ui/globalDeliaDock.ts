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

/** Matches the Portal desktop chrome breakpoint (`min-width: 1025px`). */
export const DELIA_DOCK_MIN_VIEWPORT_PX = 1025;

export const DELIA_DOCK_DEFAULT_WIDTH = 440;
export const DELIA_DOCK_MIN_WIDTH = 360;
export const DELIA_DOCK_MAX_WIDTH = 640;
export const DELIA_DOCK_MAX_WORKSPACE_RATIO = 0.45;
export const DELIA_DOCK_KEYBOARD_STEP = 24;

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

export function isCompanionDockViewport(viewportWidth: number): boolean {
  return viewportWidth >= DELIA_DOCK_MIN_VIEWPORT_PX;
}

/** Smallest workspace that keeps a 360px dock at or under 45% of the split. */
export function minimumCompanionWorkspaceWidth(): number {
  return Math.ceil(DELIA_DOCK_MIN_WIDTH / DELIA_DOCK_MAX_WORKSPACE_RATIO);
}

export function resolveDeliaDockMaxWidth(workspaceWidth: number): number {
  if (!Number.isFinite(workspaceWidth) || workspaceWidth <= 0) return 0;
  const ratioCap = Math.floor(workspaceWidth * DELIA_DOCK_MAX_WORKSPACE_RATIO);
  return Math.min(DELIA_DOCK_MAX_WIDTH, Math.max(0, ratioCap));
}

export function canFitCompanionDock(workspaceWidth: number): boolean {
  return resolveDeliaDockMaxWidth(workspaceWidth) >= DELIA_DOCK_MIN_WIDTH;
}

export function shouldRenderCompanionHandle(options: {
  apps: AppItem[] | undefined;
  pathname: string;
  viewportWidth: number;
  workspaceWidth: number;
}): boolean {
  const app = findAuthorizedDeliaApp(options.apps);
  if (!app) return false;
  if (!isCompanionDockViewport(options.viewportWidth)) return false;
  if (!canFitCompanionDock(options.workspaceWidth)) return false;
  return !isDeliaFullPagePath(options.pathname, app.basePath);
}

export function shouldKeepCompanionDockOpen(options: {
  apps: AppItem[] | undefined;
  pathname: string;
  viewportWidth: number;
  workspaceWidth: number;
  requestedOpen: boolean;
}): boolean {
  if (!options.requestedOpen) return false;
  return shouldRenderCompanionHandle(options);
}

export function clampDeliaDockWidth(requested: number, workspaceWidth: number): number {
  const max = resolveDeliaDockMaxWidth(workspaceWidth);
  if (max < DELIA_DOCK_MIN_WIDTH) return max;
  return Math.min(max, Math.max(DELIA_DOCK_MIN_WIDTH, requested));
}

/** ArrowLeft widens the right dock. ArrowRight narrows it. Home/End jump to bounds. */
export function adjustDeliaDockWidth(
  current: number,
  workspaceWidth: number,
  key: string,
): number {
  const max = resolveDeliaDockMaxWidth(workspaceWidth);
  if (key === "Home") return clampDeliaDockWidth(DELIA_DOCK_MIN_WIDTH, workspaceWidth);
  if (key === "End") return clampDeliaDockWidth(max, workspaceWidth);
  if (key === "ArrowLeft") {
    return clampDeliaDockWidth(current + DELIA_DOCK_KEYBOARD_STEP, workspaceWidth);
  }
  if (key === "ArrowRight") {
    return clampDeliaDockWidth(current - DELIA_DOCK_KEYBOARD_STEP, workspaceWidth);
  }
  return clampDeliaDockWidth(current, workspaceWidth);
}

/** Visible, connected control. Display:none yields an empty client rect. */
export function isUsableFocusTarget(el: HTMLElement | null): el is HTMLElement {
  if (!el || el.isConnected === false) return false;
  if (typeof el.getClientRects === "function" && el.getClientRects().length === 0) {
    return false;
  }
  return true;
}

export function resolveFocusReturnTarget(
  trigger: HTMLElement | null,
  fallbacks: Array<HTMLElement | null>,
): HTMLElement | null {
  if (isUsableFocusTarget(trigger)) return trigger;
  for (const candidate of fallbacks) {
    if (isUsableFocusTarget(candidate)) return candidate;
  }
  return null;
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
