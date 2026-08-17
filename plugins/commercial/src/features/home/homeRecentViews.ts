import type { PluginNavigationTarget } from "../../app/pluginRoutes";
import type { HubCapabilities } from "../../content/pluginRouteCatalog";
import { HUB_SECTIONS } from "../../content/pluginRouteCatalog";

const STORAGE_KEY = "commercial.home.recentViews.v1";
const MAX_RECENTS = 5;

export type RecentHubView = {
  viewId: PluginNavigationTarget;
  search?: string;
  label: string;
  at: number;
};

function dedupeKey(item: Pick<RecentHubView, "viewId" | "search">): string {
  return `${item.viewId}::${item.search ?? ""}`;
}

function isKnownView(viewId: string, search?: string): boolean {
  return HUB_SECTIONS.some((section) =>
    section.routes.some(
      (route) =>
        route.viewId === viewId && (route.search ?? undefined) === (search ?? undefined),
    ),
  );
}

export function readRecentViews(): RecentHubView[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as RecentHubView[];
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(
        (item) =>
          item &&
          typeof item.viewId === "string" &&
          typeof item.label === "string" &&
          isKnownView(item.viewId, item.search),
      )
      .slice(0, MAX_RECENTS);
  } catch {
    return [];
  }
}

export function pushRecentView(item: Omit<RecentHubView, "at">): RecentHubView[] {
  const nextItem: RecentHubView = { ...item, at: Date.now() };
  const key = dedupeKey(nextItem);
  const previous = readRecentViews().filter((entry) => dedupeKey(entry) !== key);
  const next = [nextItem, ...previous].slice(0, MAX_RECENTS);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }
  return next;
}

export function filterRecentsByCaps(
  items: readonly RecentHubView[],
  capabilities: HubCapabilities,
): RecentHubView[] {
  return items.filter((item) => {
    for (const section of HUB_SECTIONS) {
      for (const route of section.routes) {
        if (route.viewId !== item.viewId) continue;
        if ((route.search ?? undefined) !== (item.search ?? undefined)) continue;
        return route.requiredCap === "always" || capabilities[route.requiredCap];
      }
    }
    return false;
  });
}
