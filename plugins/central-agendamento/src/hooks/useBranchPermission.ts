import { useEffect, useState } from "react";

import { fetchMeProfile } from "../api/schedulingApi";
import type { BranchCode } from "../constants/scheduling";
import {
  approvePermissionForBranch,
  managePermissionForBranch,
} from "../constants/scheduling";

export function useBranchPermission(branch: BranchCode | null) {
  const [canManage, setCanManage] = useState(false);
  const [canApprove, setCanApprove] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      if (!branch) {
        setCanManage(false);
        setCanApprove(false);
        setCurrentUserId(null);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const profile = await fetchMeProfile();
        if (!active) return;

        const permissions = profile.permissions ?? [];
        const isSuperadmin = Boolean(profile.is_superadmin);
        const managePerm = managePermissionForBranch(branch);
        const approvePerm = approvePermissionForBranch(branch);

        setCanManage(isSuperadmin || permissions.includes(managePerm));
        setCanApprove(isSuperadmin || permissions.includes(approvePerm));
        setCurrentUserId(String(profile.id));
      } catch {
        if (active) {
          setCanManage(false);
          setCanApprove(false);
          setCurrentUserId(null);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      active = false;
    };
  }, [branch]);

  return { canManage, canApprove, currentUserId, loading };
}
