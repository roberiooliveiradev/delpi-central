import { useCallback, useEffect, useRef, useState } from "react";

import { getDowntimeFilterOptions } from "../api/mesApi";
import type { BranchCode } from "../constants/routes";
import type { DowntimeFilterOptionsResponse } from "../types/mes";

type OptionsSnapshot = {
  branch: BranchCode;
  data: DowntimeFilterOptionsResponse | null;
  error: string | null;
};

/** Opções de filtro (motivos do catálogo + origens válidas) — um fetch por
 * filial, sem exigir a permissão administrativa de Cadastros. O estado é
 * associado à filial: opções de outro contexto nunca são expostas, nem por
 * um único render. */
export function useDowntimeFilterOptions(branch: BranchCode) {
  const [snapshot, setSnapshot] = useState<OptionsSnapshot | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => {
    const requestBranch = branch;
    const next = new AbortController();
    controller.current?.abort();
    controller.current = next;
    getDowntimeFilterOptions(requestBranch, next.signal)
      .then((response) => {
        if (!next.signal.aborted) {
          setSnapshot({ branch: requestBranch, data: response, error: null });
        }
      })
      .catch((reason: unknown) => {
        if (!next.signal.aborted) {
          setSnapshot({
            branch: requestBranch,
            data: null,
            error: reason instanceof Error ? reason.message : "Falha ao carregar as opções de filtro.",
          });
        }
      });
    return () => next.abort();
  }, [branch, reloadKey]);

  const retry = useCallback(() => setReloadKey((key) => key + 1), []);
  const matches = snapshot !== null && snapshot.branch === branch;
  return {
    data: matches ? snapshot.data : null,
    error: matches ? snapshot.error : null,
    loading: !matches,
    retry,
  };
}
