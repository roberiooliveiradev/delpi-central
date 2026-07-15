import { configureHttpClient } from "./api/httpClient";
import { useScrapMonitoringRouterPath } from "./hooks/useScrapMonitoringRouterPath";
import { ScrapMonitoringPage } from "./pages/ScrapMonitoringPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useScrapMonitoringRouterPath(pathnameFromHost);

  return <ScrapMonitoringPage pathname={pathname} />;
}
