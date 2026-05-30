import { useContext, useMemo } from "react";
import { AuthContext } from "../state/AuthContext";
import type { AppItem } from "../data/coreApi";

export function useAppsById(): Record<string, AppItem> {
  const { apps } = useContext(AuthContext);

  return useMemo(
    () => Object.fromEntries(apps.map((app) => [app.id, app])),
    [apps],
  );
}
