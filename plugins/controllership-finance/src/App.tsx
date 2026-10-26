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
import { CatalogsAdminPage } from "./features/closing/CatalogsAdminPage";
import { ClaraConsentPage } from "./features/closing/ClaraConsentPage";
import { ChecklistAdminPage } from "./features/closing/ChecklistAdminPage";
import { ClosingChecklistPage } from "./features/closing/ClosingChecklistPage";
import { CockpitPage } from "./features/closing/CockpitPage";
import { FinancialSettlementsPage } from "./features/closing/FinancialSettlementsPage";
import { MonthlyClosingPage } from "./features/closing/MonthlyClosingPage";
import { PackagesPage } from "./features/closing/PackagesPage";
import { PendenciesPage } from "./features/closing/PendenciesPage";
import { StockInventoryPage } from "./features/closing/StockInventoryPage";
import { HomePage } from "./features/home/HomePage";
import { MyTasksPage } from "./features/me/MyTasksPage";
import { ProfilePage } from "./features/me/ProfilePage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  getFreshAccessToken?: () => Promise<string | undefined>;
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
        ) : resolved.view === "checklist_admin" ? (
          <ChecklistAdminPage />
        ) : resolved.view === "catalogs_admin" ? (
          <CatalogsAdminPage />
        ) : resolved.view === "my_tasks" ? (
          <MyTasksPage />
        ) : resolved.view === "profile" ? (
          <ProfilePage />
        ) : resolved.view === "clara_consent" ? (
          <ClaraConsentPage />
        ) : resolved.view === "pendencies" ? (
          <PendenciesPage />
        ) : resolved.view === "packages" ? (
          <PackagesPage period={resolved.checklistPeriod} />
        ) : resolved.view === "cockpit" ? (
          <CockpitPage period={resolved.checklistPeriod} />
        ) : resolved.view === "monthly_closing" ? (
          <MonthlyClosingPage
            basePath={basePath}
            period={resolved.checklistPeriod}
          />
        ) : (
          <NotFoundPage basePath={basePath} />
        )}
      </PluginErrorBoundary>
    </PluginShell>
  );
}

export default function App({
  getAccessToken,
  getFreshAccessToken,
  pathname,
  basePath,
}: AppProps) {
  configureHttpClient(
    getAccessToken ?? (() => undefined),
    getFreshAccessToken,
  );
  const base = normalizeBasePath(basePath);

  return (
    <ViewerContextProvider>
      <AppRoutes basePath={base} pathnameFromHost={pathname} />
    </ViewerContextProvider>
  );
}
