// src/routes/ProtectedRoute.jsx

import { useContext } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { Loader } from "../ui/Loader";
import {
  normalizeRequiredPermissions,
  userHasAnyPermission,
} from "../utils/routePermission";

interface Props {
  /** Permissão única, lista any-of, ou omitida (pública). */
  permission?: string | string[] | null;
  /** ANY-OF explícito do Core (`anyOfPermissions`). */
  anyOfPermissions?: string[] | null;
  children: React.ReactNode;
}

export const ProtectedRoute = ({
  permission,
  anyOfPermissions,
  children,
}: Props) => {
  const { user, coreLoaded } = useContext(AuthContext);
  const location = useLocation();

  if (!coreLoaded) {
    return <Loader />;
  }

  if (!user) {
    return <Navigate to="/unauthorized" replace />;
  }

  if (user.is_superadmin) {
    return <>{children}</>;
  }

  const required = normalizeRequiredPermissions(permission, anyOfPermissions);

  if (required.length === 0) {
    return <>{children}</>;
  }

  if (!userHasAnyPermission(user.permissions, required)) {
    return (
      <Navigate
        to="/unauthorized"
        replace
        state={{ from: location.pathname, permission: required[0], anyOfPermissions: required }}
      />
    );
  }

  return <>{children}</>;
};
