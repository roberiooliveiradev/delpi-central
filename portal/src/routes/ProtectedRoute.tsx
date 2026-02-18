// src/routes/ProtectedRoute.tsx

import { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";

interface Props {
  permission?: string;
  children: React.ReactNode;
}

export const ProtectedRoute = ({ permission, children }: Props) => {
  const { user } = useContext(AuthContext);

  if (!user) {
    return <Navigate to="/unauthorized" replace />;
  }

  // SUPERADMIN BYPASS
  if ((user as any).is_superadmin) {
    return <>{children}</>;
  }

  if (!permission) {
    return <>{children}</>;
  }

  const hasPermission = user.permissions?.includes(permission);

  if (!hasPermission) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};
