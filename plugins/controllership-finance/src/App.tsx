import { PluginErrorBoundary } from "@delpi/plugin-ui/index";

import { configureHttpClient } from "./api/httpClient";
import { NotFoundPage } from "./app/NotFoundPage";
import { PluginShell } from "./app/PluginShell";
import { ViewerContextProvider } from "./app/ViewerContext";
import {
  normalizeBasePath,
  resolvePluginRoute,
} from "./app/pluginRoutes";
import { usePluginRouterPath } from "./app/usePluginRouterPath";
import { ClosingChecklistPage } from "./features/closing/ClosingChecklistPage";
import { FinancialSettlementsPage } from "./features/closing/FinancialSettlementsPage";
import { StockInventoryPage } from "./features/closing/StockInventoryPage";
import { HomePage } from "./features/home/HomePage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  basePath?: string;
  search?: string;
};

function AppRoutes({
  basePath,
  pathnameFromHost,
}: {
  basePath: string;
  pathnameFromHost?: string;
}) {
  const pathname = usePluginRouterPath(pathnameFromHost, basePath);
  const resolved = resolvePluginRoute(pathname, basePath);

  return (
    <PluginShell view={resolved.view} basePath={basePath}>
      <PluginErrorBoundary
        prefix="cf"
        labels={{
          title: "Não foi possível carregar esta área",
          message: "Tente recarregar a página.",
          retry: "Recarregar",
        }}
        onError={(error) =>
          console.error("[controllership-finance] render", error)
        }
      >
        {resolved.view === "home" ? (
          <HomePage basePath={basePath} />
        ) : resolved.view === "financial_settlements" ? (
          <FinancialSettlementsPage />
        ) : resolved.view === "stock_inventory" ? (
          <StockInventoryPage />
        ) : resolved.view === "checklist" ? (
          <ClosingChecklistPage period={resolved.checklistPeriod} />
        ) : (
          <NotFoundPage basePath={basePath} />
        )}
      </PluginErrorBoundary>
    </PluginShell>
  );
}

export default function App({
  getAccessToken,
  pathname,
  basePath,
}: AppProps) {
  configureHttpClient(getAccessToken ?? (() => undefined));
  const base = normalizeBasePath(basePath);

  return (
    <ViewerContextProvider>
      <AppRoutes basePath={base} pathnameFromHost={pathname} />
    </ViewerContextProvider>
  );
}
