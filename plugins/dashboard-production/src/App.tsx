import { configureHttpClient } from "./api/httpClient";
import { PRODUCTION_ROUTES } from "./constants/routes";
import { useProductionRouterPath } from "./hooks/useProductionRouterPath";
import { DashboardProductionPage } from "./pages/DashboardProductionPage";
import { OtdPage } from "./pages/OtdPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

function normalizePath(pathname: string): string {
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

function renderPage(path: string, pathnameFromHost?: string) {
  if (path === PRODUCTION_ROUTES.otd || path.startsWith(`${PRODUCTION_ROUTES.otd}/`)) {
    return <OtdPage pathname={path} />;
  }

  return <DashboardProductionPage pathname={pathnameFromHost ?? path} />;
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useProductionRouterPath(pathnameFromHost);
  const path = normalizePath(pathname);

  return (
    <div className="dp-app-shell" key={path}>
      {renderPage(path, pathnameFromHost)}
    </div>
  );
}
