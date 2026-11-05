import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { QueryClientProvider } from "@tanstack/react-query";

import {
  authzFingerprint,
  getReportQueryClient,
  isReportSessionSealed,
  readTokenSubject,
  reconcileReportCacheScope,
  sealReportSession,
  subscribeReportCacheScope,
} from "./reportQueryCache";
import type { ReportCacheScope } from "./reportQueryKeys";

/** Contexto observado sem sessão. Distinto da ausência de provider. */
export const reportCacheUnauthenticated = { state: "unauthenticated" } as const;

const ReportCacheScopeContext = createContext<
  ReportCacheScope | typeof reportCacheUnauthenticated | null
>(null);

export function useReportCacheScope():
  | ReportCacheScope
  | typeof reportCacheUnauthenticated
  | null {
  return useContext(ReportCacheScopeContext);
}

export function useReportSessionSealed(): boolean {
  const [, setEpoch] = useState(0);
  useEffect(
    () => subscribeReportCacheScope(() => setEpoch((value) => value + 1)),
    [],
  );
  return isReportSessionSealed();
}

export function ControllershipQueryProvider({
  getAccessToken,
  permissions,
  isSuperadmin,
  children,
}: {
  getAccessToken?: () => string | undefined;
  permissions?: readonly string[];
  isSuperadmin?: boolean;
  children: ReactNode;
}) {
  const [, setEpoch] = useState(0);
  useEffect(
    () => subscribeReportCacheScope(() => setEpoch((value) => value + 1)),
    [],
  );
  useEffect(() => {
    const onLogout = () => {
      sealReportSession(readTokenSubject(getAccessToken?.()));
    };
    window.addEventListener("DELPI_GLOBAL_LOGOUT", onLogout);
    return () => window.removeEventListener("DELPI_GLOBAL_LOGOUT", onLogout);
  }, [getAccessToken]);

  const scope = reconcileReportCacheScope(
    readTokenSubject(getAccessToken?.()),
    authzFingerprint(permissions, isSuperadmin),
  );

  return (
    <QueryClientProvider client={getReportQueryClient()}>
      <ReportCacheScopeContext.Provider value={scope ?? reportCacheUnauthenticated}>
        {children}
      </ReportCacheScopeContext.Provider>
    </QueryClientProvider>
  );
}
