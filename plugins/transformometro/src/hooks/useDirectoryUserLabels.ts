import { useEffect, useMemo, useState } from "react";

import { lookupDirectoryUsers } from "../data/api/directoryUsersApi";

export type DirectoryNameFor = (
  userId: string | null | undefined,
  fallback?: string | null,
) => string;

/**
 * Resolve ids Minha Delpi → nome via lookup do core-api.
 * Nunca renderizar user_id cru na UI.
 */
export function useDirectoryUserLabels(
  userIds: readonly (string | null | undefined)[],
  getAccessToken?: () => string | undefined,
) {
  const [byId, setById] = useState<Record<string, string>>({});

  const key = useMemo(() => {
    const unique = [
      ...new Set(userIds.map((id) => (id ?? "").trim()).filter(Boolean)),
    ];
    unique.sort();
    return unique.join("|");
  }, [userIds]);

  useEffect(() => {
    if (!key) {
      setById({});
      return;
    }
    const ids = key.split("|");
    const controller = new AbortController();
    void lookupDirectoryUsers(ids, controller.signal, getAccessToken)
      .then((items) => {
        if (controller.signal.aborted) return;
        const next: Record<string, string> = {};
        for (const item of items) {
          if (item.id && item.name) next[item.id] = item.name;
        }
        setById(next);
      })
      .catch(() => {
        if (!controller.signal.aborted) setById({});
      });
    return () => controller.abort();
  }, [getAccessToken, key]);

  const nameFor = useMemo((): DirectoryNameFor => {
    return (userId, fallback) => {
      const id = (userId ?? "").trim();
      if (!id) return (fallback ?? "").trim() || "Nome indisponível";
      const hit = byId[id];
      if (hit) return hit;
      const fb = (fallback ?? "").trim();
      return fb || "Nome indisponível";
    };
  }, [byId]);

  return { byId, nameFor };
}
