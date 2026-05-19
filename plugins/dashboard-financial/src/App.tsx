import { configureHttpClient } from "./api/httpClient";
import { FINANCIAL_ROUTES } from "./constants/routes";
import { useFinancialRouterPath } from "./hooks/useFinancialRouterPath";
import { DashboardFinancialPage } from "./pages/DashboardFinancialPage";
import { EbitdaPage } from "./pages/EbitdaPage";
import { FixedCostPage } from "./pages/FixedCostPage";
import { PmrPage } from "./pages/PmrPage";
import { RolPage } from "./pages/RolPage";

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
  if (path === FINANCIAL_ROUTES.rol || path.startsWith(`${FINANCIAL_ROUTES.rol}/`)) {
    return <RolPage pathname={path} />;
  }

  if (
    path === FINANCIAL_ROUTES.ebitda ||
    path.startsWith(`${FINANCIAL_ROUTES.ebitda}/`)
  ) {
    return <EbitdaPage pathname={path} />;
  }

  if (
    path === FINANCIAL_ROUTES.fixedCost ||
    path.startsWith(`${FINANCIAL_ROUTES.fixedCost}/`)
  ) {
    return <FixedCostPage pathname={path} />;
  }

  if (path === FINANCIAL_ROUTES.pmr || path.startsWith(`${FINANCIAL_ROUTES.pmr}/`)) {
    return <PmrPage pathname={path} />;
  }

  return <DashboardFinancialPage pathname={path} />;
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useFinancialRouterPath(pathnameFromHost);
  const path = normalizePath(pathname);

  return (
    <div className="ds-app-shell" key={path}>
      {renderPage(path)}
    </div>
  );
}
