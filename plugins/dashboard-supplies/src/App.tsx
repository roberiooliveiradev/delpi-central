import { configureHttpClient } from "./api/httpClient";
import { SUPPLIES_ROUTES } from "./constants/routes";
import { useSuppliesRouterPath } from "./hooks/useSuppliesRouterPath";
import { CpvPage } from "./pages/CpvPage";
import { DashboardSuppliesPage } from "./pages/DashboardSuppliesPage";
import { InventoryTurnoverPage } from "./pages/InventoryTurnoverPage";
import { NegotiationSavingsPage } from "./pages/NegotiationSavingsPage";
import { OtdPage } from "./pages/OtdPage";
import { StockPage } from "./pages/StockPage";

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
  if (path === SUPPLIES_ROUTES.cpv || path.startsWith(`${SUPPLIES_ROUTES.cpv}/`)) {
    return <CpvPage pathname={path} />;
  }

  if (path === SUPPLIES_ROUTES.otd || path.startsWith(`${SUPPLIES_ROUTES.otd}/`)) {
    return <OtdPage pathname={path} />;
  }

  if (
    path === SUPPLIES_ROUTES.stock ||
    path.startsWith(`${SUPPLIES_ROUTES.stock}/`)
  ) {
    return <StockPage pathname={path} />;
  }

  if (
    path === SUPPLIES_ROUTES.inventoryTurnover ||
    path.startsWith(`${SUPPLIES_ROUTES.inventoryTurnover}/`)
  ) {
    return <InventoryTurnoverPage pathname={path} />;
  }

  if (
    path === SUPPLIES_ROUTES.negotiationSavings ||
    path.startsWith(`${SUPPLIES_ROUTES.negotiationSavings}/`)
  ) {
    return <NegotiationSavingsPage pathname={path} />;
  }

  return <DashboardSuppliesPage pathname={path} />;
}

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useSuppliesRouterPath(pathnameFromHost);
  const path = normalizePath(pathname);

  return (
    <div className="ds-app-shell" key={path}>
      {renderPage(path)}
    </div>
  );
}
