// portal/src/ui/admin/rbac/useAdminUserAccessProfile.ts

import { useCallback, useEffect, useRef, useState } from "react";

import type { UserAccessProfile } from "../../../data/userAccessProfileTypes";
import { useAdminApi } from "../../../hooks/useAdminApi";

type LoadOptions = {
  silent?: boolean;
};

export function useAdminUserAccessProfile(userId: string, enabled = true) {
  const [data, setData] = useState<UserAccessProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasDataRef = useRef(false);

  const api = useAdminApi();

  const load = useCallback(
    async (options?: LoadOptions) => {
      if (!userId || !enabled) {
        return;
      }

      const silent = Boolean(options?.silent && hasDataRef.current);

      if (!silent) {
        setLoading(true);
      }
      setError(null);

      try {
        const result = await api.getAdminUserAccessProfile(userId);
        setData(result);
        hasDataRef.current = true;
      } catch (err) {
        if (!silent) {
          setData(null);
          hasDataRef.current = false;
        }
        setError(
          err instanceof Error
            ? err.message
            : "Falha ao carregar perfil de acesso do usuário",
        );
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [api, enabled, userId],
  );

  useEffect(() => {
    if (!enabled) {
      return;
    }
    void load();
  }, [enabled, load]);

  return {
    data,
    loading,
    error,
    load,
  };
}
