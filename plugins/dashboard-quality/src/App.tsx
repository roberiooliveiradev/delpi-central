import { configureHttpClient } from "./api/httpClient";
import { QUALITY_ROUTES } from "./constants/routes";
import { useQualityRouterPath } from "./hooks/useQualityRouterPath";
import { Audit5sPage } from "./pages/Audit5sPage";
import { DashboardQualityPage } from "./pages/DashboardQualityPage";
import { KaizenDetailPage } from "./pages/KaizenDetailPage";
import { KaizenPage } from "./pages/KaizenPage";
import { NonconformitiesPage } from "./pages/NonconformitiesPage";
import { NonconformityDetailPage } from "./pages/NonconformityDetailPage";
import { PerdasPage } from "./pages/PerdasPage";
import { PpmItemDetailPage } from "./pages/PpmItemDetailPage";
import { PpmPage } from "./pages/PpmPage";
import { parseQualityPath } from "./utils/routeParser";

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

function renderPage(path: string, pathname?: string) {
  const route = parseQualityPath(path);

  if (route.view === "kaizen-detail") {
    return <KaizenDetailPage kaizenId={route.kaizenId} pathname={path} />;
  }

  if (route.view === "ppm-detail") {
    return <PpmItemDetailPage pathname={path} />;
  }

  if (route.view === "nonconformity-detail") {
    return <NonconformityDetailPage pathname={path} />;
  }

  if (path === QUALITY_ROUTES.ppm) {
    return <PpmPage pathname={path} />;
  }

  if (path === QUALITY_ROUTES.nonconformities) {
    return <NonconformitiesPage pathname={path} />;
  }

  if (path === QUALITY_ROUTES.perdas) {
    return <PerdasPage pathname={path} />;
  }

  if (path === QUALITY_ROUTES.kaizen) {
    return <KaizenPage pathname={path} />;
  }

  if (path === QUALITY_ROUTES.audit5s || path.startsWith(`${QUALITY_ROUTES.audit5s}/`)) {
    return <Audit5sPage pathname={path} />;
  }

  return <DashboardQualityPage pathname={pathname ?? path} />;
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useQualityRouterPath(pathnameFromHost);
  const path = normalizePath(pathname);

  return (
    <div className="dq-app-shell" key={path}>
      {renderPage(path, pathname)}
    </div>
  );
}
