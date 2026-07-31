import { createContext, useContext, type ReactNode } from "react";

import { canManageTemplates } from "../utils/tvDashboardPermissions";

type Session = {
  permissions: string[];
  isSuperadmin: boolean;
  canManageTemplates: boolean;
};

const defaultSession: Session = {
  permissions: [],
  isSuperadmin: false,
  canManageTemplates: false,
};

const Ctx = createContext<Session>(defaultSession);

export function TvDashboardSessionProvider({
  permissions,
  isSuperadmin,
  children,
}: {
  permissions?: string[];
  isSuperadmin?: boolean;
  children: ReactNode;
}) {
  const value: Session = {
    permissions: permissions ?? [],
    isSuperadmin: Boolean(isSuperadmin),
    canManageTemplates: canManageTemplates({
      permissions,
      isSuperadmin,
    }),
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTvDashboardSession() {
  return useContext(Ctx);
}
