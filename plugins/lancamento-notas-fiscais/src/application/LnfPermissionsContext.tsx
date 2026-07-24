import { useEffect, useMemo, useState, type ReactNode } from "react";
import { fetchMeProfile } from "../data/api/meApi";
import {
  resolveLnfPermissions,
  type LnfPermissionFlags,
} from "../domain/permissions";
import {
  LnfPermissionsContext,
  type LnfPermissionsState,
} from "./lnfPermissionsContextValue";

export function LnfPermissionsProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [flags, setFlags] = useState<LnfPermissionFlags>(() =>
    resolveLnfPermissions([]),
  );
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetchMeProfile()
      .then((me) => {
        if (cancelled) return;
        setUserId(me.id);
        setUserName(me.name || me.email);
        setFlags(resolveLnfPermissions(me.permissions, Boolean(me.is_superadmin)));
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar permissões.");
        setFlags(resolveLnfPermissions([]));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [tick]);

  const value = useMemo<LnfPermissionsState>(
    () => ({
      ...flags,
      loading,
      error,
      userId,
      userName,
      refresh: () => setTick((n) => n + 1),
    }),
    [flags, loading, error, userId, userName],
  );

  return (
    <LnfPermissionsContext.Provider value={value}>
      {children}
    </LnfPermissionsContext.Provider>
  );
}
