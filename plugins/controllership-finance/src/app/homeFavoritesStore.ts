import {
  getHomeFavorites,
  putHomeFavorites,
  type HomeFavoriteItem,
} from "../api/homeFavoritesApi";

type Listener = (items: HomeFavoriteItem[]) => void;

let cache: HomeFavoriteItem[] | null = null;
const listeners = new Set<Listener>();

function emit(): void {
  const snapshot = cache ?? [];
  for (const listener of listeners) {
    listener(snapshot);
  }
}

/** Snapshot atual (pode estar vazio antes do primeiro load). */
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

/** Atualiza cache local e notifica (otimista / rollback). */
export function setHomeFavoritesLocal(items: HomeFavoriteItem[]): void {
  cache = items;
  emit();
}

export async function refreshHomeFavorites(
  signal?: AbortSignal,
): Promise<HomeFavoriteItem[]> {
  const items = await getHomeFavorites(signal);
  cache = items;
  emit();
  return items;
}

export async function replaceHomeFavorites(
  items: HomeFavoriteItem[],
  signal?: AbortSignal,
): Promise<HomeFavoriteItem[]> {
  const saved = await putHomeFavorites(items, signal);
  cache = saved;
  emit();
  return saved;
}
