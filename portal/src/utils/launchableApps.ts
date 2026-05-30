import type { AppItem } from "../data/coreApi";

type AppLike = Pick<AppItem, "type"> | { type?: AppItem["type"] } | null | undefined;

export function isLaunchableApp(app: AppLike): boolean {
  return !!app && app.type !== "backend-only";
}

export function filterLaunchableApps<T extends { type?: AppItem["type"] }>(
  apps: T[],
): T[] {
  return apps.filter(isLaunchableApp);
}
