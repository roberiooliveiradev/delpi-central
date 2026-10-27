/** UX-009 — resolução de perfil de participantes (nome oficial + foto).
 *
 * Mesmo padrão de Minhas Solicitações (`useParticipantAvatarUrls`):
 * 1. `POST /closing/participants/lookup` resolve `display_name` oficial
 *    (diretório Core, bearer do usuário) e `has_photo` (person-profile);
 * 2. somente ids com `has_photo` disparam o GET de avatar (evita 404
 *    desnecessário) → `URL.createObjectURL` com revogação no cleanup.
 *
 * Perfil ausente/indisponível ⇒ campos `null` — o consumidor decide o
 * fallback (iniciais do kit), nunca UUID nem foto inventada.
 */
import { useEffect, useMemo, useRef, useState } from "react";

import {
  downloadParticipantAvatar,
  lookupParticipants,
} from "../../api/participantsApi";

export type ParticipantVisual = {
  displayName: string | null;
  photoUrl: string | null;
};

export function useParticipantProfiles(
  userIds: readonly (string | null | undefined)[],
): ReadonlyMap<string, ParticipantVisual> {
  const [profiles, setProfiles] = useState<Map<string, ParticipantVisual>>(
    () => new Map(),
  );
  const urlsRef = useRef<string[]>([]);

  const joinedIds = userIds.join("|");
  const key = useMemo(() => {
    const unique = [
      ...new Set(
        userIds.map((id) => (id ?? "").trim()).filter(Boolean),
      ),
    ];
    unique.sort();
    return unique.join("|");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [joinedIds]);

  useEffect(() => {
    // Revoga URLs do ciclo anterior — troca de documento não acumula blobs.
    for (const url of urlsRef.current) URL.revokeObjectURL(url);
    urlsRef.current = [];
    if (!key) return;
    const ids = key.split("|");
    const controller = new AbortController();
    const created: string[] = [];

    void (async () => {
      let lookup;
      try {
        lookup = await lookupParticipants(ids, {
          signal: controller.signal,
        });
      } catch {
        if (!controller.signal.aborted) setProfiles(new Map());
        return;
      }
      if (controller.signal.aborted) return;

      const next = new Map<string, ParticipantVisual>();
      for (const item of lookup.items) {
        next.set(item.user_id, {
          displayName: item.display_name,
          photoUrl: null,
        });
      }
      const canBlob = typeof URL.createObjectURL === "function";
      await Promise.all(
        lookup.items
          .filter((item) => item.has_photo && canBlob)
          .map(async (item) => {
            try {
              const blob = await downloadParticipantAvatar(item.user_id, {
                signal: controller.signal,
              });
              if (controller.signal.aborted) return;
              const url = URL.createObjectURL(blob);
              created.push(url);
              next.set(item.user_id, {
                displayName: item.display_name,
                photoUrl: url,
              });
            } catch {
              /* sem foto — permanece fallback de iniciais */
            }
          }),
      );
      if (controller.signal.aborted) {
        for (const url of created) URL.revokeObjectURL(url);
        return;
      }
      urlsRef.current.push(...created);
      setProfiles(next);
    })();

    return () => {
      controller.abort();
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [key]);

  // Revoga URLs ainda vivas quando o componente desmonta.
  useEffect(
    () => () => {
      for (const url of urlsRef.current) URL.revokeObjectURL(url);
      urlsRef.current = [];
    },
    [],
  );

  // Sem ids resolvidos, perfis stale não vazam para outro contexto.
  return key ? profiles : EMPTY_PROFILES;
}

const EMPTY_PROFILES: ReadonlyMap<string, ParticipantVisual> = new Map();
