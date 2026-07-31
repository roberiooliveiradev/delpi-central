import { useEffect, useState } from "react";

import { fetchMeProfile } from "../api/meApi";
import {
  resolveReportsPermissions,
  type ReportsPermissionFlags,
  type ReportsPermissionInput,
} from "./reportsPermissions";

const LOADING: ReportsPermissionFlags = {
  canUseAdminNav: false,
  canUseFollowUpNav: false,
};

function hostProvidesPermissions(input: ReportsPermissionInput): boolean {
  return (
    input.isSuperadmin === true ||
    typeof input.hasPermission === "function" ||
    Array.isArray(input.permissions)
  );
}

/**
 * Prefere props do portal (`permissions` / `hasPermission`);
 * em standalone, consulta `/core-api/me`.
 */
export function useReportsPermissions(
  input: ReportsPermissionInput,
): { flags: ReportsPermissionFlags; ready: boolean } {
  const hostReady = hostProvidesPermissions(input);
  const flagsFromHost = hostReady ? resolveReportsPermissions(input) : null;

  const [fetched, setFetched] = useState<ReportsPermissionFlags | null>(null);
  const [fetchReady, setFetchReady] = useState(false);

  useEffect(() => {
    if (hostReady) {
      return;
    }
    const controller = new AbortController();
    void (async () => {
      try {
        const me = await fetchMeProfile(controller.signal);
        if (controller.signal.aborted) return;
        setFetched(
          resolveReportsPermissions({
            permissions: me.permissions,
            isSuperadmin: me.is_superadmin,
          }),
        );
      } catch {
        if (controller.signal.aborted) return;
        setFetched(LOADING);
      } finally {
        if (!controller.signal.aborted) {
          setFetchReady(true);
        }
      }
    })();
    return () => controller.abort();
  }, [hostReady]);

  return {
    flags: flagsFromHost ?? fetched ?? LOADING,
    ready: hostReady || fetchReady,
  };
}
