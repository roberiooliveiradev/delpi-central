import { createContext, useContext, type ReactNode } from "react";

export const TRANSFORMOMETRO_ACCESS_PERMISSION = "transformometro.access";
export const TRANSFORMOMETRO_MANAGE_PERMISSION = "transformometro.manage";

type PortalChromeValue = {
  canManage: boolean;
  isSuperadmin: boolean;
  permissions: readonly string[];
  getAccessToken?: () => string | undefined;
};

const PortalChromeContext = createContext<PortalChromeValue>({
  canManage: false,
  isSuperadmin: false,
  permissions: [],
});

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
  const codes = permissions ?? [];
  const superadmin = isSuperadmin === true;
  const canManage =
    superadmin || codes.includes(TRANSFORMOMETRO_MANAGE_PERMISSION);
  return (
    <PortalChromeContext.Provider
      value={{
        canManage,
        isSuperadmin: superadmin,
        permissions: codes,
        getAccessToken,
      }}
    >
      {children}
    </PortalChromeContext.Provider>
  );
}

export function useCanManagePortal(): boolean {
  return useContext(PortalChromeContext).canManage;
}

export function usePortalSessionAccess(): {
  canManage: boolean;
  isSuperadmin: boolean;
  permissions: readonly string[];
} {
  const { canManage, isSuperadmin, permissions } = useContext(PortalChromeContext);
  return { canManage, isSuperadmin, permissions };
}

export function usePortalAccessToken(): (() => string | undefined) | undefined {
  return useContext(PortalChromeContext).getAccessToken;
}
