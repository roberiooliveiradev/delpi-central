import { useEffect, useState } from "react";
import {
  fetchPublicOperationAppointments,
  type PublicOperationAppointments,
} from "./api";

export type PublicOperationAppointmentsState = {
  data: PublicOperationAppointments | null;
  loading: boolean;
  error: string | null;
};

/** Histórico de apontamentos da OP+operação — compartilhado entre detalhe e modal. */
export function usePublicOperationAppointments(
  token: string,
  branch: string,
  productionOrder: string,
  operationCode: string,
): PublicOperationAppointmentsState {
  const [data, setData] = useState<PublicOperationAppointments | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    void fetchPublicOperationAppointments(token, branch, productionOrder, operationCode)
      .then((next) => {
        if (!active) return;
        setData(next);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Apontamentos indisponíveis.");
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
