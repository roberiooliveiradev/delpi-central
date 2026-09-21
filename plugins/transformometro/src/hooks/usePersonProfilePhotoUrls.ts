import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  downloadPersonProfilePhoto,
  lookupPersonProfilePhotoFlags,
} from "../data/api/transformometroInteractionApi";

/**
 * Batch blob URLs for person-profile photos (authors, mentions, speakers).
 * Soft-fail: missing/denied photos resolve to null (initials in the kit).
 */
export function usePersonProfilePhotoUrls(
  userIds: readonly (string | null | undefined)[],
  getAccessToken?: () => string | undefined,
): { photoFor: (userId: string | null | undefined) => string | null } {
  const [urlsById, setUrlsById] = useState<Record<string, string>>({});
  const urlsRef = useRef(urlsById);
  urlsRef.current = urlsById;

  const key = useMemo(() => {
    const unique = [...new Set(userIds.map((id) => (id ?? "").trim()).filter(Boolean))];
    unique.sort();
    return unique.join("|");
  }, [userIds]);

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
      try {
        const flags = await lookupPersonProfilePhotoFlags(ids, getAccessToken);
        if (cancelled) return;
        const withPhoto = (flags.items ?? [])
          .filter((item) => item.has_photo && item.user_id)
          .map((item) => item.user_id);
        const next: Record<string, string> = {};
        await Promise.all(
          withPhoto.map(async (userId) => {
            try {
              const blob = await downloadPersonProfilePhoto(userId, getAccessToken);
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
      } catch {
        if (cancelled) return;
        setUrlsById((previous) => {
          for (const url of Object.values(previous)) URL.revokeObjectURL(url);
          return {};
        });
      }
    })();
    return () => {
      cancelled = true;
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [getAccessToken, key]);

  useEffect(() => {
    return () => {
      for (const url of Object.values(urlsRef.current)) URL.revokeObjectURL(url);
    };
  }, []);

  const photoFor = useCallback(
    (userId: string | null | undefined) => {
      const id = (userId ?? "").trim();
      if (!id) return null;
      return urlsById[id] ?? null;
    },
    [urlsById],
  );

  return { photoFor };
}
