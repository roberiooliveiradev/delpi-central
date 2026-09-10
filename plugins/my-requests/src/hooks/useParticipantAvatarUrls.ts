import { useEffect, useMemo, useState } from "react";

import {
  downloadParticipantAvatarBlob,
  lookupParticipantsHasPhoto,
} from "../api/requestsApi";

/**
 * Resolve Portal avatars (via requests-api BFF → Core) for unique author ids.
 * Missing/404 → key absent (MessageThread falls back to initials).
 */
export function useParticipantAvatarUrls(
  userIds: readonly (string | null | undefined)[],
): ReadonlyMap<string, string> {
  const [byId, setById] = useState<Map<string, string>>(() => new Map());

  const key = useMemo(() => {
    const unique = [
      ...new Set(userIds.map((id) => (id ?? "").trim()).filter(Boolean)),
    ];
    unique.sort();
    return unique.join("|");
  }, [userIds]);

  useEffect(() => {
    if (!key) {
      setById(new Map());
      return;
    }
    const ids = key.split("|");
    const controller = new AbortController();
    const created: string[] = [];

    void (async () => {
      const next = new Map<string, string>();
      let withPhoto = new Set(ids);
      try {
        const lookup = await lookupParticipantsHasPhoto(ids, {
          signal: controller.signal,
        });
        if (lookup.length) {
          withPhoto = new Set(
            lookup.filter((row) => row.has_photo).map((row) => row.user_id),
          );
        }
      } catch {
        // Fall through: attempt photo GETs for all unique ids.
      }

      await Promise.all(
        ids.map(async (uid) => {
          if (!withPhoto.has(uid)) return;
          try {
            const blob = await downloadParticipantAvatarBlob(uid, {
              signal: controller.signal,
            });
            if (controller.signal.aborted) return;
            const url = URL.createObjectURL(blob);
            created.push(url);
            next.set(uid, url);
          } catch {
            /* no photo / abort */
          }
        }),
      );
      if (controller.signal.aborted) {
        for (const url of created) URL.revokeObjectURL(url);
        return;
      }
      setById(next);
    })();

    return () => {
      controller.abort();
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [key]);

  return byId;
}
