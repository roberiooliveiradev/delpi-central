import { useEffect, useMemo, useState } from "react";

import { lookupDirectoryUsers } from "../api/commercialPortfolioApi";
import type { DirectoryUser } from "../types/portfolio";
import {
  directoryUserLabelOrFallback,
  formatDirectoryUserLabel,
} from "../shared/directoryUserLabel";

/**
 * Resolve ids Minha Delpi → nome/e-mail via lookup do core-api.
 * Uso: nunca renderizar `user_id` cru na UI.
 */
export function useDirectoryUserLabels(userIds: readonly string[]) {
  const [byId, setById] = useState<Record<string, DirectoryUser>>({});

  const key = useMemo(() => {
    const unique = [...new Set(userIds.map((id) => id.trim()).filter(Boolean))];
    unique.sort();
    return unique.join("|");
  }, [userIds]);

  useEffect(() => {
    if (!key) {
      setById({});
      return;
    }
    const ids = key.split("|");
    const controller = new AbortController();
    lookupDirectoryUsers(ids, controller.signal)
      .then((items) => {
        if (controller.signal.aborted) return;
        const next: Record<string, DirectoryUser> = {};
        for (const item of items) {
          if (item?.id) next[item.id] = item;
        }
        setById(next);
      })
      .catch(() => {
        if (!controller.signal.aborted) setById({});
      });
    return () => controller.abort();
  }, [key]);

  const labelFor = useMemo(
    () => (userId: string, fallback?: string | null) => {
      const id = userId.trim();
      const hit = byId[id];
      if (hit) return formatDirectoryUserLabel(hit) || directoryUserLabelOrFallback({}, fallback);
      return directoryUserLabelOrFallback({}, fallback);
    },
    [byId],
  );

  return { byId, labelFor };
}
