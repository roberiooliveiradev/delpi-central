import type { PluginRoutableView } from "../../app/pluginRoutes";
import type { HubCapabilities } from "../../content/pluginRouteCatalog";
import { HUB_SECTIONS } from "../../content/pluginRouteCatalog";

const STORAGE_KEY = "supplies.home.favorites.v1";
const MAX_FAVORITES = 12;

export type HomeFavoriteItem = {
  viewId: PluginRoutableView;
  label: string;
};

function isKnownView(viewId: string): boolean {
  return HUB_SECTIONS.some((section) =>
    section.routes.some((route) => route.viewId === viewId),
  );
}

export function readFavorites(): HomeFavoriteItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as HomeFavoriteItem[];
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(
        (item) =>
          item &&
          typeof item.viewId === "string" &&
          typeof item.label === "string" &&
          isKnownView(item.viewId),
      )
      .slice(0, MAX_FAVORITES);
  } catch {
    return [];
  }
}

export function writeFavorites(items: HomeFavoriteItem[]): HomeFavoriteItem[] {
  const next = items
    .filter((item) => isKnownView(item.viewId))
    .slice(0, MAX_FAVORITES);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }
  return next;
}

export function toggleFavorite(
  item: HomeFavoriteItem,
  current: readonly HomeFavoriteItem[] = readFavorites(),
): HomeFavoriteItem[] {
  const exists = current.some((entry) => entry.viewId === item.viewId);
  const next = exists
    ? current.filter((entry) => entry.viewId !== item.viewId)
    : [...current, item];
  return writeFavorites([...next]);
}

export function filterFavoritesByCaps(
  items: readonly HomeFavoriteItem[],
  capabilities: HubCapabilities,
): HomeFavoriteItem[] {
  return items.filter((item) => {
    for (const section of HUB_SECTIONS) {
      for (const route of section.routes) {
        if (route.viewId !== item.viewId) continue;
        return route.requiredCap === "always" || capabilities[route.requiredCap];
      }
    }
    return false;
  });
}
