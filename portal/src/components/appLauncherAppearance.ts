import { useEffect, useMemo, useState, type CSSProperties } from "react";

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

const MOTION_CLEAR_MS = 760;

export function buildAppRoutesSignature(
  routes: ReadonlyArray<AppLauncherRouteLike>,
): string {
  return routes
    .map((route) => `${route.path}|${route.label ?? ""}`)
    .sort()
    .join("\n");
}

export function resetAppLauncherAppearanceRegistry(): void {
  snapshots.clear();
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

export function launcherMotionIndexStyle(
  motionIndex?: number,
): CSSProperties | undefined {
  if (motionIndex == null || motionIndex <= 0) {
    return undefined;
  }

  return { "--launcher-motion-index": String(motionIndex) } as CSSProperties;
}
