import { useEffect, useState } from "react";
import {
  fetchPublicWorkCenterDowntimeItems,
  type PublicWorkCenterDowntimeItems,
} from "./api";

export type PublicWorkCenterDowntimeItemsState = {
  data: PublicWorkCenterDowntimeItems | null;
  loading: boolean;
  error: string | null;
};

/** Paradas de hoje no turno atual do posto — só carrega quando o modal abre. */
export function usePublicWorkCenterDowntimeItems(
  token: string,
  branch: string,
  workCenter: string | null,
  enabled: boolean,
): PublicWorkCenterDowntimeItemsState {
  const [data, setData] = useState<PublicWorkCenterDowntimeItems | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || !workCenter) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);
    void fetchPublicWorkCenterDowntimeItems(token, branch, workCenter)
      .then((next) => {
        if (!active) return;
        setData(next);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Paradas do turno indisponíveis.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token, branch, workCenter, enabled]);

  return { data, loading, error };
}
