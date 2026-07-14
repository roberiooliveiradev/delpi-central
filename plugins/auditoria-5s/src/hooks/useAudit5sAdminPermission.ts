import { useEffect, useState } from "react";

import { fetchMeProfile } from "../api/meApi";
import { isAdminPath } from "../constants/audit5s";
import { hasAdminPermission } from "../utils/audit5sPermissions";

/**
 * Ações administrativas na UI só na rota `/filial-XX/admin` + permissão
 * `auditoria-5s.admin.filial-XX` (ou superadmin).
 */
export function useAudit5sAdminPermission(
  branch: string | null | undefined,
  pathname?: string | null,
): {
  canAdmin: boolean;
  loading: boolean;
} {
  const onAdminRoute = isAdminPath(pathname ?? undefined);
  const [hasPermission, setHasPermission] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const profile = await fetchMeProfile();
        if (!cancelled) {
          setHasPermission(hasAdminPermission(profile, branch));
        }
      } catch {
        if (!cancelled) {
          setHasPermission(false);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [branch]);

  return {
    canAdmin: onAdminRoute && hasPermission,
    loading: loading || false,
  };
}
