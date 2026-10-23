import { useEffect, useState } from "react";

import { httpGetBlob, suppliesApiUrl } from "../api/httpClient";

/**
 * Shared object-URL cache for authenticated person photos.
 *
 * Many rows can render the same requester — fetch once per photo path and
 * reuse the blob URL for the session (bounded: a handful of people).
 */
const photoCache = new Map<string, Promise<string | null>>();

/** Scope sent to the BFF photo proxy — it re-checks the caller's
 * authorized requester facet for this branch+period before serving bytes. */
export type PersonPhotoScope = {
  branches: readonly string[];
  dateFrom?: string | null;
  dateTo?: string | null;
};

function fetchPhotoObjectUrl(
  photoPath: string,
  scope?: PersonPhotoScope,
): Promise<string | null> {
  const path = photoPath.trim();
  if (!path || !scope || scope.branches.length === 0) {
    return Promise.resolve(null);
  }
  const params = new URLSearchParams();
  for (const branch of scope.branches) params.append("branch", branch);
  if (scope.dateFrom?.trim()) params.set("date_from", scope.dateFrom.trim());
  if (scope.dateTo?.trim()) params.set("date_to", scope.dateTo.trim());
  const scopedPath = `${path}?${params.toString()}`;
  let cached = photoCache.get(scopedPath);
  if (!cached) {
    cached = httpGetBlob(suppliesApiUrl(scopedPath))
      .then((blob) => (blob.size > 0 ? URL.createObjectURL(blob) : null))
      .catch(() => null);
    photoCache.set(scopedPath, cached);
  }
  return cached;
}

/** Resolves a BFF photo path to a blob URL; null while loading or on failure. */
export function usePersonPhoto(
  photoPath?: string | null,
  scope?: PersonPhotoScope,
): string | null {
  const [src, setSrc] = useState<string | null>(null);
  const scopeKey = scope
    ? `${scope.branches.join(",")}|${scope.dateFrom ?? ""}|${scope.dateTo ?? ""}`
    : "";
  useEffect(() => {
    let cancelled = false;
    if (!photoPath || !scope || scope.branches.length === 0) {
      return undefined;
    }
    void fetchPhotoObjectUrl(photoPath, scope).then((url) => {
      if (!cancelled) setSrc(url);
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [photoPath, scopeKey]);
  return photoPath && scope && scope.branches.length ? src : null;
}
