import { useLocation } from "react-router-dom";

import type { AppItem } from "../data/coreApi";
import { resolveManifestRoutePermission } from "../utils/manifestRoutePermission";
import { ProtectedRoute } from "./ProtectedRoute";

type FederatedAppRouteGuardProps = {
  app: AppItem;
  fallbackPermission?: string;
  children: React.ReactNode;
};

export function FederatedAppRouteGuard({
  app,
  fallbackPermission,
  children,
}: FederatedAppRouteGuardProps) {
  const location = useLocation();
  const permission = resolveManifestRoutePermission(
    app.routes,
    location.pathname,
    fallbackPermission,
  );

  return <ProtectedRoute permission={permission}>{children}</ProtectedRoute>;
}
