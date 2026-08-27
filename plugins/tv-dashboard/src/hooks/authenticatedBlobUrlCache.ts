import { httpGetBlob } from "../api/httpClient";

type CacheEntry = {
  blobUrl?: string;
  refCount: number;
  promise?: Promise<string>;
};

const cache = new Map<string, CacheEntry>();

function releaseEntry(apiUrl: string) {
  const entry = cache.get(apiUrl);
  if (!entry) return;
  entry.refCount -= 1;
  if (entry.refCount <= 0) {
    if (entry.blobUrl) URL.revokeObjectURL(entry.blobUrl);
    cache.delete(apiUrl);
  }
}

function fetchBlobUrl(apiUrl: string): Promise<string> {
  const existing = cache.get(apiUrl);
  if (existing?.blobUrl) {
    return Promise.resolve(existing.blobUrl);
  }
  if (existing?.promise) {
    return existing.promise;
  }

  const promise = httpGetBlob(apiUrl)
    .then((blob) => {
      const blobUrl = URL.createObjectURL(blob);
      const current = cache.get(apiUrl);
      if (current) {
        current.blobUrl = blobUrl;
        delete current.promise;
      }
      return blobUrl;
    })
    .catch((error) => {
      const current = cache.get(apiUrl);
      if (current && !current.blobUrl) {
        cache.delete(apiUrl);
      }
      throw error;
    });

  if (existing) {
    existing.promise = promise;
  } else {
    cache.set(apiUrl, { refCount: 0, promise });
  }
  return promise;
}

/** Reserva entrada no cache compartilhado (refCount). */
export function acquireAuthenticatedBlobUrl(apiUrl: string): {
  blobUrl: string | undefined;
  loading: boolean;
  release: () => void;
} {
  let entry = cache.get(apiUrl);
  if (!entry) {
    entry = { refCount: 0 };
    cache.set(apiUrl, entry);
  }
  entry.refCount += 1;

  if (entry.blobUrl) {
    return { blobUrl: entry.blobUrl, loading: false, release: () => releaseEntry(apiUrl) };
  }

  void fetchBlobUrl(apiUrl);
  return { blobUrl: undefined, loading: true, release: () => releaseEntry(apiUrl) };
}

/** Prefetch — aquece o cache; caller deve chamar release ao desmontar. */
export function prefetchAuthenticatedBlobUrl(apiUrl: string): () => void {
  const reserved = acquireAuthenticatedBlobUrl(apiUrl);
  void fetchBlobUrl(apiUrl);
  return reserved.release;
}

export function fetchAuthenticatedBlobUrl(apiUrl: string): Promise<string> {
  return fetchBlobUrl(apiUrl);
}

/** Testes — limpa cache entre casos. */
export function resetAuthenticatedBlobUrlCacheForTests() {
  for (const [apiUrl, entry] of cache.entries()) {
    if (entry.blobUrl) URL.revokeObjectURL(entry.blobUrl);
    cache.delete(apiUrl);
  }
}

export function getAuthenticatedBlobUrlCacheSizeForTests(): number {
  return cache.size;
}