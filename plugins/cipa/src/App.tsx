import { configureHttpClient } from "./api/httpClient";
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
  return <CipaAppShell route={route} />;
}
