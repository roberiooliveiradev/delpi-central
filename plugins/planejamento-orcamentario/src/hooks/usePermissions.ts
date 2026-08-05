import { useEffect, useState } from "react";

import { HttpRequestError } from "../api/httpClient";
import { fetchMeProfile, type MeProfile } from "../api/meApi";

export function usePermissions(enabled = true) {
  const [profile, setProfile] = useState<MeProfile | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const controller = new AbortController();
    setLoading(true);

    fetchMeProfile(controller.signal)
      .then((data) => {
        setProfile(data);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setError("Sessão expirada. Faça login novamente.");
        } else {
          setError("Não foi possível carregar suas permissões.");
        }
        setProfile(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [enabled]);

  return {
    profile,
    loading: enabled ? loading : false,
    error,
  };
}
