import { configureHttpClient } from "./api/httpClient";
import { useCipaAccess } from "./hooks/useCipaAccess";
import { useCipaRouterPath, parseCipaRoute } from "./hooks/useCipaRouterPath";
import { CipaAppShell } from "./pages/CipaAppShell";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  /** Permissões do portal (/core-api/me) — evita round-trip a /apps/cipa-api/access. */
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
  const pathname = useCipaRouterPath(pathnameFromHost);
  const route = parseCipaRoute(pathname);
  const { access, loading, error } = useCipaAccess(getAccessToken, {
    permissions,
    isSuperadmin,
  });
  return (
    <CipaAppShell route={route} access={access} accessLoading={loading} accessError={error} />
  );
}
