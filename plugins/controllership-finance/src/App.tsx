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
  receivedDocumentsBase,
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
import { DreHomePage } from "./features/home/DreHomePage";
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

const DRE_SURFACES = new Set(["dre_home", "received_documents"]);

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

  // DRE-019/RW02 — rede de segurança do destinatário externo: usuário
  // sem `access` mas com capability DRE (`access.dre` oficial ou a
  // legada `closing-documents.read`) que chegue a uma rota interna
  // (deep link, F5, URL copiada) retorna à sua experiência autorizada —
  // Home DRE para `access.dre`, projeção documental compat para a
  // legada. A BFF continua sendo a autoridade — isto é somente o
  // retorno seguro da UI.
  const dreViewer =
    viewer !== null &&
    viewer.capabilities.access !== true &&
    viewer.capabilities.accessDre === true;
  const legacyRecipientOnly =
    viewer !== null &&
    viewer.capabilities.access !== true &&
    viewer.capabilities.accessDre !== true &&
    viewer.capabilities.closingDocumentsRead === true;
  useEffect(() => {
    if (dreViewer && !DRE_SURFACES.has(resolved.view)) {
      navigatePluginView("dre_home", { basePath, replace: true });
      return;
    }
    if (
      legacyRecipientOnly &&
      resolved.view !== "received_documents"
    ) {
      navigatePluginView("received_documents", {
        basePath,
        replace: true,
      });
    }
  }, [dreViewer, legacyRecipientOnly, resolved.view, basePath]);

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
        ) : resolved.view === "dre_home" ? (
          <DreHomePage basePath={basePath} />
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
            receivedBase={receivedDocumentsBase(resolved.relativePath)}
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
