import {
  readFavorites,
  writeFavorites,
  toggleFavorite,
  type HomeFavoriteItem,
} from "../features/home/homeFavorites";

type Listener = (items: HomeFavoriteItem[]) => void;

let cache: HomeFavoriteItem[] | null = null;
const listeners = new Set<Listener>();

function emit(): void {
  const snapshot = cache ?? [];
  for (const listener of listeners) {
    listener(snapshot);
  }
}

export function getHomeFavoritesSnapshot(): HomeFavoriteItem[] {
  return cache ?? [];
}

export function subscribeHomeFavorites(listener: Listener): () => void {
  listeners.add(listener);
  if (cache !== null) {
    listener(cache);
  }
  return () => {
    listeners.delete(listener);
  };
}

/** Carrega favoritos do localStorage e notifica assinantes. */
export function loadHomeFavoritesFromStorage(): HomeFavoriteItem[] {
  const items = readFavorites();
  cache = items;
  emit();
  return items;
}

export function setHomeFavorites(items: HomeFavoriteItem[]): HomeFavoriteItem[] {
  const saved = writeFavorites(items);
  cache = saved;
  emit();
  return saved;
}

export function toggleHomeFavorite(item: HomeFavoriteItem): HomeFavoriteItem[] {
  const current = cache ?? readFavorites();
  const next = toggleFavorite(item, current);
  cache = next;
  emit();
  return next;
}

export function removeHomeFavorite(viewId: HomeFavoriteItem["viewId"]): HomeFavoriteItem[] {
  const current = cache ?? readFavorites();
  const next = writeFavorites(current.filter((entry) => entry.viewId !== viewId));
  cache = next;
  emit();
  return next;
}

/** Reinicia cache em testes. */
export function resetHomeFavoritesStoreForTests(): void {
  cache = null;
  listeners.clear();
}
