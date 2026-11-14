import { useContext } from "react";
import { useLocation } from "react-router-dom";

import type { AppItem } from "../data/coreApi";
import { AuthContext } from "../state/AuthContext";
import {
  hasAuthorizedAppEntry,
  resolveManifestRouteAccess,
} from "../utils/manifestRoutePermission";
import { userHasAnyPermission } from "../utils/routePermission";
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
  const access = resolveManifestRouteAccess(
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
    access.required.length > 0 &&
    !userHasAnyPermission(user.permissions, access.required) &&
    hasAuthorizedAppEntry(app.routes, location.pathname, app.basePath)
  ) {
    return <>{children}</>;
  }

  return (
    <ProtectedRoute
      permission={access.permission}
      anyOfPermissions={access.anyOfPermissions}
    >
      {children}
    </ProtectedRoute>
  );
}
