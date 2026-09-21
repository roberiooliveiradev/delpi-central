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

const MODAL_FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(", ");

/** Visible, connected control. Display:none yields an empty client rect. */
export function isUsableFocusTarget(el: HTMLElement | null): el is HTMLElement {
  if (!el || el.isConnected === false) return false;
  if (typeof el.getClientRects === "function" && el.getClientRects().length === 0) {
    return false;
  }
  return true;
}

/**
 * Focus returns to the trigger that opened the panel when it is still usable.
 * Otherwise the first still-visible launcher. Transient only.
 */
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

export function listModalFocusables(root: ParentNode): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(MODAL_FOCUSABLE_SELECTOR)).filter(
    (el) => isUsableFocusTarget(el),
  );
}

/** Tab cycles inside the dialog. Focus outside the list lands on the first item. */
export function resolveModalTabTarget(
  focusables: HTMLElement[],
  active: Element | null,
  shiftKey: boolean,
): HTMLElement | null {
  if (!focusables.length) return null;
  const index = focusables.findIndex((el) => el === active);
  if (index < 0) return shiftKey ? focusables[focusables.length - 1] : focusables[0];
  if (shiftKey) {
    return focusables[index === 0 ? focusables.length - 1 : index - 1];
  }
  return focusables[index === focusables.length - 1 ? 0 : index + 1];
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
