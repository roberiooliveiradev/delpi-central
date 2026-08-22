import { useEffect, useMemo, useState } from "react";

import { getAccess, type TravelAccess } from "../api/travelExpensesApi";
import { buildAccessFromPermissions } from "../security/travelAccess";

type Options = {
  permissions?: string[];
  isSuperadmin?: boolean;
};

export function useTravelAccess(getAccessToken?: () => string | undefined, options: Options = {}) {
  const permissionCodes = options.permissions;
  const isSuperadmin = Boolean(options.isSuperadmin);
  const canResolveLocally = Array.isArray(permissionCodes);

  const localAccess = useMemo(
    () => (canResolveLocally ? buildAccessFromPermissions(permissionCodes, isSuperadmin) : null),
    [canResolveLocally, isSuperadmin, permissionCodes],
  );

  const [remoteAccess, setRemoteAccess] = useState<TravelAccess | null>(null);
  const [loading, setLoading] = useState(!canResolveLocally);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (canResolveLocally) {
      setRemoteAccess(null);
      setError(null);
      setLoading(false);
      return;
    }

    let active = true;
    setLoading(true);
    getAccess()
      .then((data) => {
        if (!active) return;
        setRemoteAccess(data);
        setError(null);
      })
      .catch((err: Error) => {
        if (!active) return;
        setRemoteAccess(null);
        setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [canResolveLocally, getAccessToken]);

  return {
    access: localAccess ?? remoteAccess,
    loading,
    error,
  };
}
