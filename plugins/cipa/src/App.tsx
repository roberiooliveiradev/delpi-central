import { configureHttpClient } from "./api/httpClient";
import { useCipaAccess } from "./hooks/useCipaAccess";
import { useCipaRouterPath, parseCipaRoute } from "./hooks/useCipaRouterPath";
import { CipaAppShell } from "./pages/CipaAppShell";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const pathname = useCipaRouterPath(pathnameFromHost);
  const route = parseCipaRoute(pathname);
  const { access, loading, error } = useCipaAccess(getAccessToken);
  return (
    <CipaAppShell route={route} access={access} accessLoading={loading} accessError={error} />
  );
}
