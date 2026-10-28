import { useContext } from "react";
import { Navigate, useLocation } from "react-router-dom";

import type { AppItem } from "../data/coreApi";
import { AuthContext } from "../state/AuthContext";
import {
  resolveAuthorizedEntryPath,
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

  // Entrada multi-público (DRE-019-RW01): no basePath exato, usuário sem a
  // permission da rota raiz mas COM rotas autorizadas no app é direcionado
  // à sua entrada — mesma convenção do launcher. Rotas internas negadas
  // continuam /unauthorized; quem não tem rota alguma nunca chega aqui.
  if (
    coreLoaded &&
    user &&
    !user.is_superadmin &&
    permission &&
    !user.permissions.includes(permission)
  ) {
    const entryPath = resolveAuthorizedEntryPath(
      app.routes,
      location.pathname,
      app.basePath,
    );
    if (entryPath) {
      return <Navigate to={entryPath} replace />;
    }
  }

  return <ProtectedRoute permission={permission}>{children}</ProtectedRoute>;
}
