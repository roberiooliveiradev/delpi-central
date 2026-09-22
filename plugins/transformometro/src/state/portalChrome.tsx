import { createContext, useContext, type ReactNode } from "react";

const MANAGE_PERMISSION = "transformometro.manage";

type PortalChromeValue = {
  canManage: boolean;
  getAccessToken?: () => string | undefined;
};

const PortalChromeContext = createContext<PortalChromeValue>({ canManage: false });

type PortalChromeProviderProps = {
  permissions?: readonly string[];
  isSuperadmin?: boolean;
  getAccessToken?: () => string | undefined;
  children: ReactNode;
};

/** Só esconde a navegação. Quem autoriza é a Core, no manifesto e na API. */
export function PortalChromeProvider({
  permissions,
  isSuperadmin,
  getAccessToken,
  children,
}: PortalChromeProviderProps) {
  const canManage =
    isSuperadmin === true || (permissions ?? []).includes(MANAGE_PERMISSION);
  return (
    <PortalChromeContext.Provider value={{ canManage, getAccessToken }}>
      {children}
    </PortalChromeContext.Provider>
  );
}

export function useCanManagePortal(): boolean {
  return useContext(PortalChromeContext).canManage;
}

export function usePortalAccessToken(): (() => string | undefined) | undefined {
  return useContext(PortalChromeContext).getAccessToken;
}
