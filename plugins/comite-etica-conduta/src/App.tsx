import { configureHttpClient } from "./api/httpClient";
import { useCecAccess } from "./hooks/useCecAccess";
import { useCecRouterPath, parseCecRoute } from "./hooks/useCecRouterPath";
import { CecAppShell } from "./pages/CecAppShell";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  /** Permissões do portal (/core-api/me) — evita round-trip a /apps/comite-etica-conduta-api/access. */
  permissions?: string[];
  isSuperadmin?: boolean;
};

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  permissions,
  isSuperadmin,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const pathname = useCecRouterPath(pathnameFromHost);
  const route = parseCecRoute(pathname);
  const { access, loading, error } = useCecAccess(getAccessToken, {
    permissions,
    isSuperadmin,
  });
  return (
    <CecAppShell route={route} access={access} accessLoading={loading} accessError={error} />
  );
}
