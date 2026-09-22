import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { downloadDirectoryUserPhoto } from "../api/helpdeskApi";

/**
 * Blob URLs for Minha DELPI person-profile photos keyed by directory_user_id.
 * Soft-fail: missing/denied → null (initials no avatar).
 */
export function useDirectoryUserPhotoUrls(
  entries: readonly { directoryUserId?: string; hasPhoto?: boolean }[],
): { photoFor: (directoryUserId: string | null | undefined) => string | null } {
  const [urlsById, setUrlsById] = useState<Record<string, string>>({});
  const urlsRef = useRef(urlsById);
  urlsRef.current = urlsById;

  const key = useMemo(() => {
    const unique = [
      ...new Set(
        entries
          .filter((row) => row.hasPhoto && (row.directoryUserId || "").trim())
          .map((row) => (row.directoryUserId || "").trim()),
      ),
    ];
    unique.sort();
    return unique.join("|");
  }, [entries]);

  useEffect(() => {
    if (!key) {
      setUrlsById((previous) => {
        for (const url of Object.values(previous)) URL.revokeObjectURL(url);
        return {};
      });
      return;
    }
    const ids = key.split("|");
    let cancelled = false;
    const created: string[] = [];
    void (async () => {
      const next: Record<string, string> = {};
      await Promise.all(
        ids.map(async (userId) => {
          try {
            const blob = await downloadDirectoryUserPhoto(userId);
            if (cancelled || !blob) return;
            const url = URL.createObjectURL(blob);
            created.push(url);
            next[userId] = url;
          } catch {
            /* soft-fail → initials */
          }
        }),
      );
      if (cancelled) {
        for (const url of created) URL.revokeObjectURL(url);
        return;
      }
      setUrlsById((previous) => {
        for (const url of Object.values(previous)) URL.revokeObjectURL(url);
        return next;
      });
      created.length = 0;
    })();
    return () => {
      cancelled = true;
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [key]);

  useEffect(() => {
    return () => {
      for (const url of Object.values(urlsRef.current)) URL.revokeObjectURL(url);
    };
  }, []);

  const photoFor = useCallback((directoryUserId: string | null | undefined) => {
    const id = (directoryUserId ?? "").trim();
    if (!id) return null;
    return urlsById[id] ?? null;
  }, [urlsById]);

  return { photoFor };
}
