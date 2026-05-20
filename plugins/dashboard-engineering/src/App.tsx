import { configureHttpClient } from "./api/httpClient";
import { ENGINEERING_ROUTES } from "./constants/routes";
import { useEngineeringRouterPath } from "./hooks/useEngineeringRouterPath";
import { DashboardEngineeringPage } from "./pages/DashboardEngineeringPage";
import { ProcessesPage } from "./pages/ProcessesPage";

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

function renderPage(path: string) {
  if (
    path === ENGINEERING_ROUTES.processes ||
    path.startsWith(`${ENGINEERING_ROUTES.processes}/`)
  ) {
    return <ProcessesPage pathname={path} />;
  }

  return <DashboardEngineeringPage pathname={path} />;
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useEngineeringRouterPath(pathnameFromHost);
  const path = normalizePath(pathname);

  return (
    <div className="ds-app-shell" key={path}>
      {renderPage(path)}
    </div>
  );
}
