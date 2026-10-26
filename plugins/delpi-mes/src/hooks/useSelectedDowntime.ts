import { useEffect, useRef, useState } from "react";

import { getDowntimes } from "../api/mesApi";
import type { BranchCode } from "../constants/routes";
import type { DowntimeItem } from "../types/mes";

/** Resolve uma ocorrência por id — consulta pontual sob demanda para o
 * detalhe/deep link, sempre escopada pela filial autorizada. */
export function useSelectedDowntime(branch: BranchCode, downtimeId: string | null) {
  const [item, setItem] = useState<DowntimeItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => {
    queueMicrotask(() => {
      setItem(null);
      setError(null);
      setLoading(Boolean(downtimeId));
    });
    if (!downtimeId) return;
    const next = new AbortController();
    controller.current?.abort();
    controller.current = next;
    getDowntimes({ branch, downtimeId, page: 1, pageSize: 1 }, next.signal)
      .then((response) => setItem(response.items[0] ?? null))
      .catch((reason: unknown) => {
        if (!next.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Falha ao carregar o detalhe da parada.");
        }
      })
      .finally(() => {
        if (!next.signal.aborted) setLoading(false);
      });
    return () => next.abort();
  }, [branch, downtimeId]);

  return { item, error, loading };
}
