import { useEffect, useMemo, useState } from "react";

import { fetchCipaAccess, type CipaAccessPayload } from "../api/cipaApi";
import { buildCipaAccessFromPermissions } from "../security/buildCipaAccess";
import type { CipaAccess } from "../security/cipaAccess";

type Options = {
  permissions?: string[];
  isSuperadmin?: boolean;
};

function normalizeAccessPayload(data: CipaAccessPayload): CipaAccess {
  return {
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
}

export function useCipaAccess(
  getAccessToken?: () => string | undefined,
  options: Options = {},
) {
  const permissionCodes = options.permissions;
  const isSuperadmin = Boolean(options.isSuperadmin);
  const canResolveLocally = Array.isArray(permissionCodes);

  const localAccess = useMemo(
    () =>
      canResolveLocally
        ? buildCipaAccessFromPermissions(permissionCodes, isSuperadmin)
        : null,
    [canResolveLocally, isSuperadmin, permissionCodes],
  );

  const [remoteAccess, setRemoteAccess] = useState<CipaAccess | null>(null);
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

    fetchCipaAccess()
      .then((data) => {
        if (!active) return;
        setRemoteAccess(normalizeAccessPayload(data));
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
