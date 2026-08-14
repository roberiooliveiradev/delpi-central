import { useEffect, useMemo, useState, type ReactNode } from "react";
import { fetchMeProfile } from "../data/api/meApi";
import {
  resolveIssuancePermissions,
  type IssuancePermissionFlags,
} from "../domain/permissions";
import {
  IssuancePermissionsContext,
  type IssuancePermissionsState,
} from "./issuancePermissionsContextValue";

export function IssuancePermissionsProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [flags, setFlags] = useState<IssuancePermissionFlags>(() =>
    resolveIssuancePermissions([]),
  );
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    fetchMeProfile()
      .then((me) => {
        if (cancelled) return;
        setUserId(me.id);
        setUserName(me.name || me.email);
        setFlags(
          resolveIssuancePermissions(me.permissions, Boolean(me.is_superadmin)),
        );
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar permissões.");
        setFlags(resolveIssuancePermissions([]));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [tick]);

  const value = useMemo<IssuancePermissionsState>(
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
    <IssuancePermissionsContext.Provider value={value}>
      {children}
    </IssuancePermissionsContext.Provider>
  );
}
