import { configureHttpClient } from "./api/httpClient";
import { QUALITY_ROUTES } from "./constants/routes";
import { DashboardQualityPage } from "./pages/DashboardQualityPage";
import { Audit5sPage } from "./pages/Audit5sPage";
import { KaizenPage } from "./pages/KaizenPage";
import { NonconformitiesPage } from "./pages/NonconformitiesPage";
import { PpmPage } from "./pages/PpmPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

function normalizePath(pathname?: string): string {
  if (!pathname) return QUALITY_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const path = normalizePath(pathname);

  if (path === QUALITY_ROUTES.ppm || path.startsWith(`${QUALITY_ROUTES.ppm}/`)) {
    return <PpmPage pathname={path} />;
  }

  if (
    path === QUALITY_ROUTES.nonconformities ||
    path.startsWith(`${QUALITY_ROUTES.nonconformities}/`)
  ) {
    return <NonconformitiesPage pathname={path} />;
  }

  if (path === QUALITY_ROUTES.kaizen || path.startsWith(`${QUALITY_ROUTES.kaizen}/`)) {
    return <KaizenPage pathname={path} />;
  }

  if (path === QUALITY_ROUTES.audit5s || path.startsWith(`${QUALITY_ROUTES.audit5s}/`)) {
    return <Audit5sPage pathname={path} />;
  }

  return <DashboardQualityPage pathname={path} />;
}
