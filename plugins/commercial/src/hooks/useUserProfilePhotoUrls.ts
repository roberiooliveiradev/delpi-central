import { useEffect, useMemo, useState } from "react";

import { httpGetBlob } from "../api/httpClient";
import {
  getUserProfile,
  userProfilePhotoAbsoluteUrl,
} from "../api/userProfileApi";

/**
 * Carrega fotos de perfil Commercial em lote (blob URLs) para diagramas / listas.
 * Sem foto ou erro → chave ausente no mapa.
 */
export function useUserProfilePhotoUrls(
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
      await Promise.all(
        ids.map(async (uid) => {
          try {
            const profile = await getUserProfile(uid, controller.signal);
            if (controller.signal.aborted || !profile.has_photo) return;
            const blob = await httpGetBlob(userProfilePhotoAbsoluteUrl(uid), {
              signal: controller.signal,
            });
            if (controller.signal.aborted) return;
            const url = URL.createObjectURL(blob);
            created.push(url);
            next.set(uid, url);
          } catch {
            /* sem foto / abort */
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
