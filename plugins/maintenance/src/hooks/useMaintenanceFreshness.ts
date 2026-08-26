import { useCallback, useState } from "react";

export function useMaintenanceFreshness() {
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const touchFreshness = useCallback(() => {
    setLastUpdatedAt(new Date());
  }, []);
  return { lastUpdatedAt, touchFreshness };
}
