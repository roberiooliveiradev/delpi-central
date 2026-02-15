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
    return <div>Carregando...</div>;
  }

  if (permission && !user.permissions.includes(permission)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};
