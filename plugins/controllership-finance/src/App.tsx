import { useEffect } from "react";

import { PluginErrorBoundary } from "@delpi/plugin-ui/index";

import { configureHttpClient } from "./api/httpClient";
import { NotFoundPage } from "./app/NotFoundPage";
import { PluginShell } from "./app/PluginShell";
import { navigatePluginView } from "./app/pluginNavigation";
import {
  ViewerContextProvider,
  useViewerContext,
} from "./app/ViewerContext";
import {
  normalizeBasePath,
  resolvePluginRoute,
} from "./app/pluginRoutes";
import { usePluginRouterPath } from "./app/usePluginRouterPath";
import { CatalogsAdminPage } from "./features/closing/CatalogsAdminPage";
import { ClaraConsentPage } from "./features/closing/ClaraConsentPage";
import { ChecklistAdminPage } from "./features/closing/ChecklistAdminPage";
import { ChecklistAdminEventsPage } from "./features/closing/ChecklistAdminEventsPage";
import { ChecklistVersionPage } from "./features/closing/ChecklistVersionPage";
import { ChecklistVersionDocumentPage } from "./features/closing/ChecklistVersionDocumentPage";
import { DocumentsAdminPage } from "./features/closing/DocumentsAdminPage";
import { ClosingChecklistPage } from "./features/closing/ClosingChecklistPage";
import { CockpitPage } from "./features/closing/CockpitPage";
import { FinancialSettlementsPage } from "./features/closing/FinancialSettlementsPage";
import { MonthlyClosingPage } from "./features/closing/MonthlyClosingPage";
import { ReceivedDocumentsPage } from "./features/closing/ReceivedDocumentsPage";
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

const DRE_SURFACES = new Set(["home", "received_documents", "not_found"]);

function AppRoutes({
  basePath,
  pathnameFromHost,
}: {
  basePath: string;
  pathnameFromHost?: string;
}) {
  const pathname = usePluginRouterPath(pathnameFromHost, basePath);
  const resolved = resolvePluginRoute(pathname, basePath);
  const { viewer } = useViewerContext();

  // RW04 — UMA Home: interno e DRE compartilham o basePath. A rota
  // `/home` existe apenas como entrada autorizada do launcher DRE e
  // canonicaliza no basePath — nunca renderiza uma página paralela.
  useEffect(() => {
    if (resolved.view === "home" && resolved.relativePath === "home") {
      navigatePluginView("home", { basePath, replace: true });
    }
  }, [resolved.view, resolved.relativePath, basePath]);

  // DRE-019 — rede de segurança do destinatário externo: usuário sem
  // `access` mas com `access.dre` que chegue a uma view interna (deep
  // link legado, mount com contexto obsoleto) retorna à Home. O guard
  // do Portal já nega essas rotas antes do mount e a BFF continua
  // autoridade — isto é somente o retorno seguro da UI.
  const dreViewer =
    viewer !== null &&
    viewer.capabilities.access !== true &&
    viewer.capabilities.accessDre === true;
  useEffect(() => {
    if (dreViewer && !DRE_SURFACES.has(resolved.view)) {
      navigatePluginView("home", { basePath, replace: true });
    }
  }, [dreViewer, resolved.view, basePath]);

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
          <ChecklistAdminPage basePath={basePath} />
        ) : resolved.view === "checklist_version" ? (
          <ChecklistVersionPage
            basePath={basePath}
            version={Number(resolved.adminVersion)}
          />
        ) : resolved.view === "checklist_version_document" ? (
          <ChecklistVersionDocumentPage
            basePath={basePath}
            version={Number(resolved.adminVersion)}
            itemKey={resolved.documentItemKey ?? ""}
          />
        ) : resolved.view === "checklist_admin_events" ? (
          <ChecklistAdminEventsPage
            basePath={basePath}
            version={
              resolved.adminVersion !== undefined
                ? Number(resolved.adminVersion)
                : null
            }
          />
        ) : resolved.view === "catalogs_admin" ? (
          <CatalogsAdminPage />
        ) : resolved.view === "documents_admin" ? (
          <DocumentsAdminPage
            basePath={basePath}
            itemKey={resolved.documentItemKey}
          />
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
            documentRef={resolved.documentRef}
            reportKey={resolved.reportKey}
          />
        ) : resolved.view === "received_documents" ? (
          <ReceivedDocumentsPage
            basePath={basePath}
            period={resolved.checklistPeriod}
            documentRef={resolved.documentRef}
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
