import { useEffect, useState } from "react";

import { fetchMeProfile } from "../api/schedulingApi";
import type { BranchCode } from "../constants/scheduling";
import { managePermissionForBranch } from "../constants/scheduling";

export function useBranchPermission(branch: BranchCode | null) {
  const [canManage, setCanManage] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      if (!branch) {
        setCanManage(false);
        setCurrentUserId(null);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const profile = await fetchMeProfile();
        if (!active) return;

        const managePerm = managePermissionForBranch(branch);
        const isManager =
          Boolean(profile.is_superadmin) ||
          (profile.permissions ?? []).includes(managePerm);
        setCanManage(isManager);
        setCurrentUserId(String(profile.id));
      } catch {
        if (active) {
          setCanManage(false);
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

  return { canManage, currentUserId, loading };
}
