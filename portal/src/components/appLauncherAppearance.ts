import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";

export type AppLauncherRouteLike = {
  path: string;
  label?: string | null;
};

export type AppLauncherAppearanceScope = "full" | "content";

export type AppLauncherAppearanceState = {
  tileClass: string;
  nameClass: string;
  pinClass: string;
  routesClass: string;
};

const EMPTY_STATE: AppLauncherAppearanceState = {
  tileClass: "",
  nameClass: "",
  pinClass: "",
  routesClass: "",
};

type Snapshot = {
  name: string;
  routesSignature: string;
  isPinned: boolean;
};

const snapshots = new Map<string, Snapshot>();
const pendingRouteIntents = new Map<string, string>();
const routeIntentListeners = new Map<string, Set<() => void>>();

const MOTION_CLEAR_MS = 760;
const ROUTE_MOTION_CLEAR_MS = 620;

export function normalizeLauncherPath(value: string): string {
  return value.replace(/\/+$/, "") || "/";
}

export function resolveActiveRouteForApp(
  routes: ReadonlyArray<AppLauncherRouteLike>,
  currentPath: string,
): string | null {
  const normalized = normalizeLauncherPath(currentPath);

  for (const route of routes) {
    if (normalizeLauncherPath(route.path) === normalized) {
      return normalized;
    }
  }

  return null;
}

export function markAppRouteNavigationIntent(appId: string, path: string): void {
  if (!appId) {
    return;
  }

  pendingRouteIntents.set(appId, normalizeLauncherPath(path));
  routeIntentListeners.get(appId)?.forEach((listener) => listener());
}

export type AppLauncherRouteNavigationState = {
  tileRouteClass: string;
  routesPanelClass: string;
  activatedRoutePath: string | null;
};

const EMPTY_ROUTE_STATE: AppLauncherRouteNavigationState = {
  tileRouteClass: "",
  routesPanelClass: "",
  activatedRoutePath: null,
};

export function resetAppLauncherAppearanceRegistry(): void {
  snapshots.clear();
  pendingRouteIntents.clear();
  routeIntentListeners.clear();
}

export function buildAppRoutesSignature(
  routes: ReadonlyArray<AppLauncherRouteLike>,
): string {
  return routes
    .map((route) => `${route.path}|${route.label ?? ""}`)
    .sort()
    .join("\n");
}

export function resolveAppLauncherAppearanceUpdate(
  appId: string,
  snapshot: Snapshot,
  scope: AppLauncherAppearanceScope,
): AppLauncherAppearanceState {
  const previous = snapshots.get(appId);
  snapshots.set(appId, snapshot);

  if (!previous) {
    if (scope === "content") {
      return EMPTY_STATE;
    }

    return { ...EMPTY_STATE, tileClass: "launcher-app-tile--appear" };
  }

  const next: AppLauncherAppearanceState = { ...EMPTY_STATE };

  if (previous.name !== snapshot.name) {
    next.nameClass = "launcher-app-name--changed";
  }

  if (previous.routesSignature !== snapshot.routesSignature) {
    next.routesClass = "launcher-inline-routes--changed";
  }

  if (previous.isPinned !== snapshot.isPinned) {
    next.pinClass = snapshot.isPinned
      ? "launcher-pin--favorited"
      : "launcher-pin--unfavorited";
    next.tileClass = snapshot.isPinned
      ? "launcher-app-tile--favorited"
      : "launcher-app-tile--unfavorited";
  }

  return next;
}

export function useAppLauncherAppearance(
  appId: string,
  options: {
    name: string;
    routes: ReadonlyArray<AppLauncherRouteLike>;
    isPinned: boolean;
    enabled?: boolean;
    scope?: AppLauncherAppearanceScope;
  },
): AppLauncherAppearanceState {
  const {
    name,
    routes,
    isPinned,
    enabled = true,
    scope = "full",
  } = options;

  const routesSignature = useMemo(
    () => buildAppRoutesSignature(routes),
    [routes],
  );

  const [state, setState] = useState<AppLauncherAppearanceState>(EMPTY_STATE);

  useEffect(() => {
    if (!enabled || !appId) {
      return;
    }

    const update = resolveAppLauncherAppearanceUpdate(
      appId,
      { name, routesSignature, isPinned },
      scope,
    );

    const hasMotion = Boolean(
      update.tileClass ||
        update.nameClass ||
        update.pinClass ||
        update.routesClass,
    );

    if (!hasMotion) {
      return;
    }

    setState(update);

    const timer = window.setTimeout(() => {
      setState(EMPTY_STATE);
    }, MOTION_CLEAR_MS);

    return () => window.clearTimeout(timer);
  }, [appId, name, routesSignature, isPinned, enabled, scope]);

  return state;
}

function resolveAppLauncherRouteNavigationUpdate(
  options: {
    routes: ReadonlyArray<AppLauncherRouteLike>;
    currentPath: string;
    isRoutesOpen: boolean;
    previousRoute: string | null | undefined;
    wasRoutesOpen: boolean;
    pendingRoute: string | null;
  },
): {
  update: AppLauncherRouteNavigationState;
  nextPreviousRoute: string | null;
} {
  const activeRoute = resolveActiveRouteForApp(options.routes, options.currentPath);

  if (options.previousRoute === undefined) {
    return {
      update: EMPTY_ROUTE_STATE,
      nextPreviousRoute: activeRoute,
    };
  }

  const next: AppLauncherRouteNavigationState = { ...EMPTY_ROUTE_STATE };
  const targetRoute =
    options.pendingRoute && options.pendingRoute !== activeRoute
      ? options.pendingRoute
      : activeRoute;

  let nextPreviousRoute = options.previousRoute ?? null;

  if (targetRoute && targetRoute !== options.previousRoute) {
    next.tileRouteClass = "launcher-app-tile--routed";
    next.activatedRoutePath = targetRoute;
    nextPreviousRoute = targetRoute;
  } else {
    nextPreviousRoute = activeRoute;
  }

  if (options.isRoutesOpen && !options.wasRoutesOpen) {
    next.routesPanelClass = "launcher-inline-routes--expand";
  }

  return { update: next, nextPreviousRoute };
}

export function useAppLauncherRouteNavigation(
  appId: string,
  options: {
    routes: ReadonlyArray<AppLauncherRouteLike>;
    currentPath: string;
    isRoutesOpen: boolean;
    enabled?: boolean;
  },
): AppLauncherRouteNavigationState {
  const {
    routes,
    currentPath,
    isRoutesOpen,
    enabled = true,
  } = options;

  const previousRouteRef = useRef<string | null | undefined>(undefined);
  const wasRoutesOpenRef = useRef(false);
  const [intentVersion, setIntentVersion] = useState(0);
  const [state, setState] = useState<AppLauncherRouteNavigationState>(
    EMPTY_ROUTE_STATE,
  );

  useEffect(() => {
    if (!appId) {
      return;
    }

    const listeners = routeIntentListeners.get(appId) ?? new Set();
    const listener = () => setIntentVersion((value) => value + 1);
    listeners.add(listener);
    routeIntentListeners.set(appId, listeners);

    return () => {
      listeners.delete(listener);
      if (listeners.size === 0) {
        routeIntentListeners.delete(appId);
      }
    };
  }, [appId]);

  useEffect(() => {
    if (!enabled || !appId) {
      return;
    }

    const pendingRoute = pendingRouteIntents.get(appId) ?? null;
    const { update, nextPreviousRoute } = resolveAppLauncherRouteNavigationUpdate({
      routes,
      currentPath,
      isRoutesOpen,
      previousRoute: previousRouteRef.current,
      wasRoutesOpen: wasRoutesOpenRef.current,
      pendingRoute,
    });

    previousRouteRef.current = nextPreviousRoute;
    wasRoutesOpenRef.current = isRoutesOpen;

    if (pendingRoute) {
      pendingRouteIntents.delete(appId);
    }

    const hasMotion = Boolean(
      update.tileRouteClass ||
        update.routesPanelClass ||
        update.activatedRoutePath,
    );

    if (!hasMotion) {
      return;
    }

    setState(update);

    const timer = window.setTimeout(() => {
      setState(EMPTY_ROUTE_STATE);
    }, ROUTE_MOTION_CLEAR_MS);

    return () => window.clearTimeout(timer);
  }, [
    appId,
    routes,
    currentPath,
    isRoutesOpen,
    enabled,
    intentVersion,
  ]);

  return state;
}

export function launcherMotionIndexStyle(
  motionIndex?: number,
): CSSProperties | undefined {
  if (motionIndex == null || motionIndex <= 0) {
    return undefined;
  }

  return { "--launcher-motion-index": String(motionIndex) } as CSSProperties;
}
