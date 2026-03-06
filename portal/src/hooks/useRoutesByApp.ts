// src/hooks/useRoutesByApp.ts

import { useContext, useMemo } from "react";
import { AuthContext } from "../state/AuthContext";
import type { RouteItem } from "../data/coreApi";

export function useRoutesByApp() {
  const { apps, routes } = useContext(AuthContext);

  return useMemo(() => {
    const map: Record<string, RouteItem[]> = {};

    apps.forEach((a) => (map[a.id] = []));

    routes.forEach((r) => {
      if (!r.app) return;

      if (!map[r.app]) {
        map[r.app] = [];
      }

      map[r.app].push(r);
    });

    return map;
  }, [apps, routes]);
}