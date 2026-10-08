import { useCallback, useEffect, useState } from "react";
import {
  fetchPublicOperationMaterials,
  type PublicOperationMaterials,
} from "./api";

export type PublicOperationMaterialsState = {
  data: PublicOperationMaterials | null;
  loading: boolean;
  error: string | null;
  /** Nova tentativa após erro (ex.: botão «Tentar novamente»). */
  reload: () => void;
};

/** Materiais SD4 da OP+operação — só busca quando `enabled` (modal aberto). */
export function usePublicOperationMaterials(
  token: string,
  branch: string,
  productionOrder: string,
  operationCode: string,
  enabled: boolean,
): PublicOperationMaterialsState {
  const [data, setData] = useState<PublicOperationMaterials | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadTick, setReloadTick] = useState(0);
  const reload = useCallback(() => setReloadTick((tick) => tick + 1), []);

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    setLoading(true);
    setError(null);
    void fetchPublicOperationMaterials(token, branch, productionOrder, operationCode)
      .then((next) => {
        if (!active) return;
        setData(next);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Materiais da operação indisponíveis.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token, branch, productionOrder, operationCode, enabled, reloadTick]);

  return { data, loading, error, reload };
}
