import { useContext } from "react";
import { useLocation } from "react-router-dom";

import type { AppItem } from "../data/coreApi";
import { AuthContext } from "../state/AuthContext";
import {
  hasAuthorizedAppEntry,
  resolveManifestRoutePermission,
} from "../utils/manifestRoutePermission";
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
  const { user, coreLoaded } = useContext(AuthContext);
  const permission = resolveManifestRoutePermission(
    app.authorizationRoutes ?? app.routes,
    location.pathname,
    fallbackPermission,
  );

  // Entrada multi-público (DRE-019-RW01/RW04): no basePath exato, usuário
  // sem a permission da rota raiz mas COM ≥1 rota autorizada no app monta
  // o MFE — a Home única é resolvida pelo próprio app por capability.
  // Não é bypass: o predicado é o mesmo do launcher (segura pelo menos
  // uma rota autorizada); rotas internas negadas continuam /unauthorized
  // e a BFF permanece a autoridade final. Quem não tem rota alguma nunca
  // chega aqui.
  if (
    coreLoaded &&
    user &&
    !user.is_superadmin &&
    permission &&
    !user.permissions.includes(permission) &&
    hasAuthorizedAppEntry(app.routes, location.pathname, app.basePath)
  ) {
    return <>{children}</>;
  }

  return <ProtectedRoute permission={permission}>{children}</ProtectedRoute>;
}
