import { useEffect, useMemo, useState } from "react";

import { downloadParticipantAvatarBlob } from "../api/participantsApi";

/**
 * Resolve Portal avatars (via engineering-api BFF → Core) for unique
 * actor ids. Always attempts GET per id; 404/error → initials fallback.
 */
export function useParticipantAvatarUrls(
  userIds: readonly (string | null | undefined)[],
): ReadonlyMap<string, string> {
  const [byId, setById] = useState<Map<string, string>>(() => new Map());

  const key = useMemo(() => {
    const unique = [
      ...new Set(
        userIds.map((id) => (id ?? "").trim()).filter(Boolean),
      ),
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
      await Promise.all(
        ids.map(async (uid) => {
          try {
            const blob = await downloadParticipantAvatarBlob(
              uid,
              controller.signal,
            );
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
