type CacheEntry<T> = {
  value: T;
  storedAt: number;
};

const CACHE_TTL_MS = 10 * 60 * 1000;
const store = new Map<string, CacheEntry<unknown>>();

export function buildStrategicIndicatorsCacheKey(
  route: string,
  params: Record<string, string | number | undefined>,
): string {
  const normalized = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== "")
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("&");

  return `${route}?${normalized}`;
}

export function getStrategicIndicatorsCachedValue<T>(key: string): T | null {
  const entry = store.get(key);
  if (!entry) {
    return null;
  }

  if (Date.now() - entry.storedAt > CACHE_TTL_MS) {
    store.delete(key);
    return null;
  }

  return entry.value as T;
}

export function setStrategicIndicatorsCachedValue<T>(key: string, value: T): void {
  store.set(key, {
    value,
    storedAt: Date.now(),
  });
}
