import {
  PORTAL_SEARCH_CATALOG,
  type PortalCatalogItem,
} from "../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import { isAdministrationFavoritePath } from "./portalFavorites";

export const PORTAL_RECENT_ACCESS_STORAGE_KEY = "transformometro.portal.recent-access.v1";
const MAX_RECENTS = 5;

export type PortalRecentAccessItem = {
  path: string;
  label: string;
};

type Listener = (items: PortalRecentAccessItem[]) => void;

const listeners = new Set<Listener>();
let memory: PortalRecentAccessItem[] | null = null;

function normalizePath(path: string): string {
  const [clean] = path.split(/[?#]/);
  if (!clean) return "";
  return clean.length > 1 && clean.endsWith("/") ? clean.slice(0, -1) : clean;
}

function aliasPath(path: string): string {
  if (path.endsWith("/ajuda")) return TRANSFORMOMETRO_ROUTES.help;
  if (path.includes("/processos")) {
    return path.replace("/processos", "/processes");
  }
  if (path.includes("/atas")) {
    return path.replace("/atas", "/meeting-minutes");
  }
  if (path.includes("/configuracoes")) {
    return path.replace("/configuracoes", "/settings");
  }
  return path;
}

export function resolveRecentAccessCatalogItem(path: string): PortalCatalogItem | null {
  const normalized = aliasPath(normalizePath(path));
  if (!normalized || normalized === TRANSFORMOMETRO_ROUTES.home) return null;
  const exact = PORTAL_SEARCH_CATALOG.find((item) => item.path === normalized);
  if (exact) return exact;
  const matches = PORTAL_SEARCH_CATALOG.filter(
    (item) =>
      item.path !== TRANSFORMOMETRO_ROUTES.home &&
      (normalized === item.path || normalized.startsWith(`${item.path}/`)),
  );
  return matches.sort((left, right) => right.path.length - left.path.length)[0] ?? null;
}

function catalogLabel(path: string): string | null {
  return resolveRecentAccessCatalogItem(path)?.label ?? null;
}

function sanitize(
  items: PortalRecentAccessItem[],
  canManage: boolean,
): PortalRecentAccessItem[] {
  const unique = new Map<string, PortalRecentAccessItem>();
  for (const item of items) {
    if (!item || typeof item.path !== "string") continue;
    const resolved = resolveRecentAccessCatalogItem(item.path);
    if (!resolved) continue;
    if (!canManage && (resolved.group === "Administração" || resolved.id === "administration")) {
      continue;
    }
    if (isAdministrationFavoritePath(resolved.path) && !canManage) continue;
    unique.set(resolved.path, { path: resolved.path, label: resolved.label });
  }
  return [...unique.values()].slice(0, MAX_RECENTS);
}

function persist(items: PortalRecentAccessItem[], canManage = true): PortalRecentAccessItem[] {
  const next = sanitize(items, canManage);
  memory = next;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(PORTAL_RECENT_ACCESS_STORAGE_KEY, JSON.stringify(next));
  }
  for (const listener of listeners) listener(next);
  return next;
}

export function readPortalRecentAccess(canManage = true): PortalRecentAccessItem[] {
  if (memory) return sanitize(memory, canManage);
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(PORTAL_RECENT_ACCESS_STORAGE_KEY);
    if (!raw) {
      memory = [];
      return memory;
    }
    const parsed = JSON.parse(raw) as PortalRecentAccessItem[];
    memory = sanitize(Array.isArray(parsed) ? parsed : [], canManage);
    return memory;
  } catch {
    memory = [];
    return memory;
  }
}

export function recordPortalRecentAccess(
  path: string,
  options?: { canManage?: boolean },
): PortalRecentAccessItem[] {
  const canManage = options?.canManage !== false;
  const resolved = resolveRecentAccessCatalogItem(path);
  if (!resolved) return readPortalRecentAccess(canManage);
  if (!canManage && (resolved.group === "Administração" || resolved.id === "administration")) {
    return readPortalRecentAccess(canManage);
  }
  const nextItem = { path: resolved.path, label: resolved.label };
  const previous = readPortalRecentAccess(canManage).filter((item) => item.path !== nextItem.path);
  return persist([nextItem, ...previous], canManage);
}

export function visiblePortalRecentAccess(
  items: readonly PortalRecentAccessItem[],
  canManage: boolean,
): PortalRecentAccessItem[] {
  return sanitize([...items], canManage);
}

export function subscribePortalRecentAccess(listener: Listener): () => void {
  listeners.add(listener);
  listener(readPortalRecentAccess());
  return () => {
    listeners.delete(listener);
  };
}

export function resetPortalRecentAccessForTests(): void {
  memory = null;
  listeners.clear();
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(PORTAL_RECENT_ACCESS_STORAGE_KEY);
  }
}

export function recentAccessCatalogLabel(path: string): string | null {
  return catalogLabel(path);
}
