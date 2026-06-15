import { configureHttpClient } from "./api/httpClient";
import { useLmpsRouterPath } from "./hooks/useLmpsRouterPath";
import { DashboardLmpsPage } from "./pages/DashboardLmpsPage";
import { LmpDetailPage } from "./pages/LmpDetailPage";
import { normalizeLmpsPath, parseLmpsPath, readOvBranchFromUrl } from "./utils/routeParser";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useLmpsRouterPath(pathnameFromHost);
  const path = normalizeLmpsPath(pathname);
  const route = parseLmpsPath(path);

  if (route.view === "ov-detail" && route.saleNumber) {
    return (
      <LmpDetailPage
        saleNumber={route.saleNumber}
        branch={readOvBranchFromUrl()}
      />
    );
  }

  return <DashboardLmpsPage pathname={path} />;
}
