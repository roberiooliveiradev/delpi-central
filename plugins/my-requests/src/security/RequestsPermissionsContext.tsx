import { createContext, useContext, type ReactNode } from "react";

import {
  buildAccessFromPermissions,
  type AppPermissions,
} from "../security/requestsAccess";

const RequestsPermissionsContext = createContext<AppPermissions | null>(null);

export function RequestsPermissionsProvider({
  permissions,
  isSuperadmin = false,
  children,
}: {
  permissions?: string[];
  isSuperadmin?: boolean;
  children: ReactNode;
}) {
  const value = buildAccessFromPermissions(permissions, isSuperadmin);
  return (
    <RequestsPermissionsContext.Provider value={value}>
      {children}
    </RequestsPermissionsContext.Provider>
  );
}

export function useRequestsPermissions(): AppPermissions {
  const ctx = useContext(RequestsPermissionsContext);
  if (!ctx) {
    throw new Error("useRequestsPermissions must be used within RequestsPermissionsProvider");
  }
  return ctx;
}
