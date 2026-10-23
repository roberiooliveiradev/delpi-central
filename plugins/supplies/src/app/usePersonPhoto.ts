import { useEffect, useState } from "react";

import { httpGetBlob, suppliesApiUrl } from "../api/httpClient";

/**
 * Shared object-URL cache for authenticated person photos.
 *
 * Many rows can render the same requester — fetch once per photo path and
 * reuse the blob URL for the session (bounded: a handful of people).
 */
const photoCache = new Map<string, Promise<string | null>>();

function fetchPhotoObjectUrl(photoPath: string): Promise<string | null> {
  const path = photoPath.trim();
  if (!path) return Promise.resolve(null);
  let cached = photoCache.get(path);
  if (!cached) {
    cached = httpGetBlob(suppliesApiUrl(path))
      .then((blob) => (blob.size > 0 ? URL.createObjectURL(blob) : null))
      .catch(() => null);
    photoCache.set(path, cached);
  }
  return cached;
}

/** Resolves a BFF photo path to a blob URL; null while loading or on failure. */
export function usePersonPhoto(photoPath?: string | null): string | null {
  const [src, setSrc] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    if (!photoPath) {
      return undefined;
    }
    void fetchPhotoObjectUrl(photoPath).then((url) => {
      if (!cancelled) setSrc(url);
    });
    return () => {
      cancelled = true;
    };
  }, [photoPath]);
  return photoPath ? src : null;
}
