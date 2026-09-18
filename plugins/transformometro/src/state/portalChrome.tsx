import { createContext, useContext, type ReactNode } from "react";

const MANAGE_PERMISSION = "transformometro.manage";

const PortalChromeContext = createContext({ canManage: false });

type PortalChromeProviderProps = {
  permissions?: readonly string[];
  isSuperadmin?: boolean;
  children: ReactNode;
};

/** Só esconde a navegação. Quem autoriza é a Core, no manifesto e na API. */
export function PortalChromeProvider({
  permissions,
  isSuperadmin,
  children,
}: PortalChromeProviderProps) {
  const canManage =
    isSuperadmin === true || (permissions ?? []).includes(MANAGE_PERMISSION);
  return (
    <PortalChromeContext.Provider value={{ canManage }}>
      {children}
    </PortalChromeContext.Provider>
  );
}

export function useCanManagePortal(): boolean {
  return useContext(PortalChromeContext).canManage;
}
