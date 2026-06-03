// src/routes/ProtectedRoute.jsx

import { useContext } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import { Loader } from "../ui/Loader";

interface Props {
  permission?: string;
  children: React.ReactNode;
}

export const ProtectedRoute = ({ permission, children }: Props) => {
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

  if (!permission) {
    return <>{children}</>;
  }

  const hasPermission = user.permissions.includes(permission);

  if (!hasPermission) {
    return (
      <Navigate
        to="/unauthorized"
        replace
        state={{ from: location.pathname, permission }}
      />
    );
  }

  return <>{children}</>;
};