import type { ReactNode } from "react";

import { PageTransition } from "./components/PageTransition";
import { ConfirmDialogProvider } from "./components/ui/ConfirmDialogProvider";
import { FloatingNoticeProvider } from "./components/ui/FloatingNoticeProvider";
import { DashboardPage } from "./ui/pages/DashboardPage";
import {
  ConfiguracoesWorkspacePage,
  isConfiguracoesWorkspaceRoute,
} from "./ui/pages/ConfiguracoesWorkspacePage";
import { ProcessoWorkspacePage, isProcessoWorkspaceRoute } from "./ui/pages/ProcessoWorkspacePage";
import { ProcessosPage } from "./ui/pages/ProcessosPage";
import { DataTransferPage } from "./ui/pages/DataTransferPage";
import { useDelpiPortalBridge } from "./hooks/useDelpiPortalBridge";
import { useTransformometroRouterPath } from "./hooks/useTransformometroRouterPath";
import { TRANSFORMOMETRO_ROUTES } from "./constants/routes";
import { buildProcessoPath, parseTransformometroPath } from "./utils/routeParser";
import { navigateTransformometro } from "./utils/navigation";
import { buildTransformometroTransitionKey } from "./utils/transitionKey";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  const pathname = useTransformometroRouterPath(pathnameFromHost);
  const route = parseTransformometroPath(pathname);
  const transitionKey = buildTransformometroTransitionKey(pathname);

  useDelpiPortalBridge(pathname);

  const onNavigate = navigateTransformometro;

  let page: ReactNode;

  if (route.view === "dashboard") {
    page = (
      <DashboardPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  } else if (route.view === "dados") {
    page = (
      <DataTransferPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  } else if (isConfiguracoesWorkspaceRoute(route)) {
    page = (
      <ConfiguracoesWorkspacePage
        getAccessToken={getAccessToken}
        route={route}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  } else if (isProcessoWorkspaceRoute(route)) {
    page = (
      <ProcessoWorkspacePage
        getAccessToken={getAccessToken}
        route={route}
        pathname={pathname}
        onNavigate={onNavigate}
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.processos)}
      />
    );
  } else if (route.view === "processos") {
    page = (
      <ProcessosPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={onNavigate}
        onOpenProcesso={(id, opts) =>
          onNavigate(
            opts?.setupInstancia
              ? `${buildProcessoPath(id)}#nova-instancia`
              : buildProcessoPath(id)
          )
        }
      />
    );
  } else {
    page = (
      <DashboardPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  }

  return (
    <ConfirmDialogProvider>
      <FloatingNoticeProvider>
        <PageTransition transitionKey={transitionKey}>{page}</PageTransition>
      </FloatingNoticeProvider>
    </ConfirmDialogProvider>
  );
}
