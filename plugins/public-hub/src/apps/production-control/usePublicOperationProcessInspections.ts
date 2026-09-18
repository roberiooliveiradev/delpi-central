import { useEffect, useState } from "react";
import {
  fetchPublicOperationProcessInspections,
  type PublicOperationProcessInspections,
} from "./api";

export type PublicOperationProcessInspectionsState = {
  data: PublicOperationProcessInspections | null;
  loading: boolean;
  error: string | null;
};

/** Inspeções de processo da OP+operação — busca ao abrir o detalhe (cor do botão + modal). */
export function usePublicOperationProcessInspections(
  token: string,
  branch: string,
  productionOrder: string,
  operationCode: string,
): PublicOperationProcessInspectionsState {
  const [data, setData] = useState<PublicOperationProcessInspections | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    void fetchPublicOperationProcessInspections(token, branch, productionOrder, operationCode)
      .then((next) => {
        if (!active) return;
        setData(next);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Inspeções da operação indisponíveis.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token, branch, productionOrder, operationCode]);

  return { data, loading, error };
}
