import { PORTAL_SEARCH_CATALOG } from "../constants/portalExperience";

export const PORTAL_FAVORITES_STORAGE_KEY = "transformometro.portal.favorites.v1";
const MAX_FAVORITES = 12;

export type PortalFavoriteItem = {
  path: string;
  label: string;
};

type Listener = (items: PortalFavoriteItem[]) => void;

const listeners = new Set<Listener>();
let memory: PortalFavoriteItem[] | null = null;

export function portalFavoriteKey(item: Pick<PortalFavoriteItem, "path">): string {
  return item.path;
}

export function isAdministrationFavoritePath(path: string): boolean {
  const item = PORTAL_SEARCH_CATALOG.find((entry) => entry.path === path);
  return item?.group === "Administração" || item?.id === "administration";
}

function catalogLabel(path: string): string | null {
  return PORTAL_SEARCH_CATALOG.find((entry) => entry.path === path)?.label ?? null;
}

function sanitize(items: PortalFavoriteItem[]): PortalFavoriteItem[] {
  const unique = new Map<string, PortalFavoriteItem>();
  for (const item of items) {
    if (!item || typeof item.path !== "string") continue;
    const label = catalogLabel(item.path);
    if (!label) continue;
    unique.set(item.path, { path: item.path, label });
  }
  return [...unique.values()].slice(0, MAX_FAVORITES);
}

function persist(items: PortalFavoriteItem[]): PortalFavoriteItem[] {
  const next = sanitize(items);
  memory = next;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(PORTAL_FAVORITES_STORAGE_KEY, JSON.stringify(next));
  }
  for (const listener of listeners) listener(next);
  return next;
}

export function readPortalFavorites(): PortalFavoriteItem[] {
  if (memory) return memory;
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(PORTAL_FAVORITES_STORAGE_KEY);
    if (!raw) {
      memory = [];
      return memory;
    }
    const parsed = JSON.parse(raw) as PortalFavoriteItem[];
    memory = sanitize(Array.isArray(parsed) ? parsed : []);
    return memory;
  } catch {
    memory = [];
    return memory;
  }
}

export function writePortalFavorites(items: PortalFavoriteItem[]): PortalFavoriteItem[] {
  return persist(items);
}

export function togglePortalFavorite(item: PortalFavoriteItem): PortalFavoriteItem[] {
  const current = readPortalFavorites();
  const exists = current.some((entry) => entry.path === item.path);
  return persist(exists ? current.filter((entry) => entry.path !== item.path) : [...current, item]);
}

export function visiblePortalFavorites(
  items: readonly PortalFavoriteItem[],
  canManage: boolean,
): PortalFavoriteItem[] {
  return items.filter((item) => canManage || !isAdministrationFavoritePath(item.path));
}

export function subscribePortalFavorites(listener: Listener): () => void {
  listeners.add(listener);
  listener(readPortalFavorites());
  return () => {
    listeners.delete(listener);
  };
}

export function resetPortalFavoritesForTests(): void {
  memory = null;
  listeners.clear();
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(PORTAL_FAVORITES_STORAGE_KEY);
  }
}
