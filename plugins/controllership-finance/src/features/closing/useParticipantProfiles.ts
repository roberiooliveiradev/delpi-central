/** UX-009-RW01 — resolução de perfil de participantes (nome oficial +
 * foto) **sempre no contexto do documento autorizado**.
 *
 * O direito de acesso depende de (competência, documento): a chave do
 * efeito inclui `period`+`documentId` e o estado resolvido é etiquetado
 * com essa chave — perfis resolvidos num contexto anterior **nunca** são
 * exibidos após a troca de documento/competência (nenhum nome/foto
 * stale). Mesmo padrão de Minhas Solicitações
 * (`useParticipantAvatarUrls`):
 * 1. `POST …/participants/lookup` resolve `display_name` oficial
 *    (diretório Core, bearer do usuário) e `has_photo` (person-profile)
 *    — a BFF devolve somente ids com vínculo canônico ao documento;
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
  type ParticipantContext,
} from "../../api/participantsApi";

export type ParticipantVisual = {
  displayName: string | null;
  photoUrl: string | null;
};

type ResolvedProfiles = {
  key: string;
  map: Map<string, ParticipantVisual>;
};

export function useParticipantProfiles(
  context: ParticipantContext,
  userIds: readonly (string | null | undefined)[],
): ReadonlyMap<string, ParticipantVisual> {
  const [resolved, setResolved] = useState<ResolvedProfiles | null>(null);
  const urlsRef = useRef<string[]>([]);

  const joinedIds = userIds.join("|");
  const key = useMemo(() => {
    const unique = [
      ...new Set(
        userIds.map((id) => (id ?? "").trim()).filter(Boolean),
      ),
    ];
    unique.sort();
    // Contexto documental integra a chave — perfis de outro
    // documento/competência nunca são reutilizados.
    return `${context.period}::${context.documentId}::${unique.join("|")}`;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [context.period, context.documentId, joinedIds]);

  useEffect(() => {
    // Revoga URLs do ciclo anterior — troca de documento não acumula
    // blobs nem perfis resolvidos sob outra autorização.
    for (const url of urlsRef.current) URL.revokeObjectURL(url);
    urlsRef.current = [];
    const ids = key.split("::").pop()!.split("|").filter(Boolean);
    const controller = new AbortController();
    const created: string[] = [];

    void (async () => {
      let lookup;
      try {
        lookup = await lookupParticipants(context, ids, {
          signal: controller.signal,
        });
      } catch {
        if (!controller.signal.aborted) {
          setResolved({ key, map: new Map() });
        }
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
              const blob = await downloadParticipantAvatar(
                context,
                item.user_id,
                { signal: controller.signal },
              );
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
      setResolved({ key, map: next });
    })();

    return () => {
      controller.abort();
      for (const url of created) URL.revokeObjectURL(url);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  // Revoga URLs ainda vivas quando o componente desmonta.
  useEffect(
    () => () => {
      for (const url of urlsRef.current) URL.revokeObjectURL(url);
      urlsRef.current = [];
    },
    [],
  );

  // Perfis resolvidos só valem para a chave corrente (contexto + ids).
  return resolved && resolved.key === key ? resolved.map : EMPTY_PROFILES;
}

const EMPTY_PROFILES: ReadonlyMap<string, ParticipantVisual> = new Map();
