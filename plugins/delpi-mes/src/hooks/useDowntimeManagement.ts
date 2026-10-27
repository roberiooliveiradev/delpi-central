import { useCallback, useEffect, useState } from "react";

import { getDowntimeHistory, getDowntimeTreatment } from "../api/mesApi";
import type { BranchCode } from "../constants/routes";
import type { DowntimeHistoryItem, DowntimeTreatment } from "../types/mes";

type ManagementSnapshot = {
  key: string;
  treatment: DowntimeTreatment | null;
  history: DowntimeHistoryItem[];
  /** Falha de consulta distinguível de "sem tratamento" — nunca confundir. */
  error: string | null;
};

/** Triagem + histórico canônico de uma parada — carregamento sob demanda,
 * escopado por filial + id. Estado associado à identidade da parada: uma
 * resposta atrasada de outra seleção nunca é exposta, nem por um render. */
export function useDowntimeManagement(branch: BranchCode, downtimeId: string | null) {
  const [snapshot, setSnapshot] = useState<ManagementSnapshot | null>(null);
  const [reloadCount, setReloadCount] = useState(0);
  const key = downtimeId ? branch + "|" + downtimeId : null;

  /** Recarrega a gestão: o bump reexecuta o effect de fetch, que aborta a
   * requisição em curso antes de iniciar a nova — sem corrida entre reloads. */
  const reload = useCallback(() => {
    setReloadCount((count) => count + 1);
  }, []);

  useEffect(() => {
    if (!key || !downtimeId) return;
    const requestKey = key;
    const controller = new AbortController();
    void (async () => {
      try {
        const [treatmentResponse, historyResponse] = await Promise.all([
          getDowntimeTreatment(downtimeId, branch, controller.signal),
          getDowntimeHistory(downtimeId, branch, controller.signal),
        ]);
        if (!controller.signal.aborted) {
          setSnapshot({
            key: requestKey,
            treatment: treatmentResponse.treatment,
            history: historyResponse.items,
            error: null,
          });
        }
      } catch (reason) {
        if (!controller.signal.aborted) {
          setSnapshot({
            key: requestKey,
            treatment: null,
            history: [],
            error:
              reason instanceof Error
                ? reason.message
                : "Falha ao carregar a gestão da parada.",
          });
        }
      }
    })();
    return () => controller.abort();
  }, [branch, downtimeId, key, reloadCount]);

  const matches = key !== null && snapshot !== null && snapshot.key === key;
  return {
    treatment: matches ? snapshot.treatment : null,
    history: matches ? snapshot.history : [],
    error: matches ? snapshot.error : null,
    loading: key !== null && !matches,
    reload,
  };
}
