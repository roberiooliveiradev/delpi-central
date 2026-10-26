import { useEffect, useRef, useState } from "react";

import { getDowntimes } from "../api/mesApi";
import type { BranchCode } from "../constants/routes";
import type { DowntimeItem } from "../types/mes";

type SelectedSnapshot = {
  key: string;
  item: DowntimeItem | null;
  error: string | null;
};

/** Resolve uma ocorrência por id — consulta pontual sob demanda para o
 * detalhe/deep link, sempre escopada pela filial autorizada. O estado é
 * associado à identidade (filial + id): uma resposta atrasada de outro
 * contexto nunca é exposta, nem por um único render. */
export function useSelectedDowntime(branch: BranchCode, downtimeId: string | null) {
  const [snapshot, setSnapshot] = useState<SelectedSnapshot | null>(null);
  const controller = useRef<AbortController | null>(null);
  const key = downtimeId ? branch + "|" + downtimeId : null;

  useEffect(() => {
    if (!key || !downtimeId) return;
    const requestKey = key;
    const next = new AbortController();
    controller.current?.abort();
    controller.current = next;
    getDowntimes({ branch, downtimeId, page: 1, pageSize: 1 }, next.signal)
      .then((response) => {
        if (!next.signal.aborted) {
          setSnapshot({ key: requestKey, item: response.items[0] ?? null, error: null });
        }
      })
      .catch((reason: unknown) => {
        if (!next.signal.aborted) {
          setSnapshot({
            key: requestKey,
            item: null,
            error: reason instanceof Error ? reason.message : "Falha ao carregar o detalhe da parada.",
          });
        }
      });
    return () => next.abort();
  }, [branch, downtimeId, key]);

  const matches = key !== null && snapshot !== null && snapshot.key === key;
  return {
    item: matches ? snapshot.item : null,
    error: matches ? snapshot.error : null,
    loading: key !== null && !matches,
  };
}
