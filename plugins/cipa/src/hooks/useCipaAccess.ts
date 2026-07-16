import { useEffect, useState } from "react";

import { fetchCipaAccess, type CipaAccessPayload } from "../api/cipaApi";
import type { CipaAccess } from "../security/cipaAccess";

type CacheEntry = {
  key: string;
  data: CipaAccess;
};

let accessCache: CacheEntry | null = null;

export function invalidateCipaAccessCache(): void {
  accessCache = null;
}

export function useCipaAccess(getAccessToken?: () => string | undefined) {
  const cacheKey = getAccessToken ? "authenticated" : "anonymous";
  const cached = accessCache?.key === cacheKey ? accessCache.data : null;

  const [access, setAccess] = useState<CipaAccess | null>(cached);
  const [loading, setLoading] = useState(!cached);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    if (accessCache?.key === cacheKey) {
      setAccess(accessCache.data);
      setError(null);
      setLoading(false);
      return () => {
        active = false;
      };
    }

    setLoading(true);
    fetchCipaAccess()
      .then((data: CipaAccessPayload) => {
        if (!active) return;
        const normalized: CipaAccess = {
          admin: Boolean(data.admin),
          can_view: Boolean(data.can_view),
          can_manage: Boolean(data.can_manage),
          can_sign: Boolean(data.can_sign),
          units: (data.units ?? []).map((unit) => ({
            id: unit.id,
            label: unit.label,
            view: Boolean(unit.view),
            manage: Boolean(unit.manage),
            sign: Boolean(unit.sign),
          })),
        };
        accessCache = { key: cacheKey, data: normalized };
        setAccess(normalized);
        setError(null);
      })
      .catch((err: Error) => {
        if (!active) return;
        setAccess(null);
        setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [cacheKey]);

  return { access, loading, error };
}
