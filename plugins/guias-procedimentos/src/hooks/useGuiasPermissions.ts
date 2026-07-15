import { useEffect, useState } from "react";

import { fetchMeProfile, type MeProfile } from "../api/meApi";
import { HttpRequestError } from "../api/httpClient";
import { hasManagePermission } from "../utils/permissions";

export function useGuiasPermissions(enabled = true) {
  const [profile, setProfile] = useState<MeProfile | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;
    setLoading(true);
    fetchMeProfile()
      .then((data) => {
        if (!cancelled) {
          setProfile(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setError("Não autenticado.");
        } else {
          setError("Não foi possível carregar permissões.");
        }
        setProfile(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return {
    profile,
    loading: enabled ? loading : false,
    error,
    canManage: hasManagePermission(profile),
  };
}
