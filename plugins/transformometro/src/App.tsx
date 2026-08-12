import type { ReactNode } from "react";

import { PageTransition } from "./components/PageTransition";
import { ConfirmDialogProvider } from "./components/ui/ConfirmDialogProvider";
import {
  UnsavedChangesGuardProvider,
  useGuardedNavigate,
} from "./components/ui/UnsavedChangesGuard";
import { FloatingNoticeProvider } from "./components/ui/FloatingNoticeProvider";
import { DashboardPage } from "./ui/pages/DashboardPage";
import {
  ConfiguracoesWorkspacePage,
  isConfiguracoesWorkspaceRoute,
} from "./ui/pages/ConfiguracoesWorkspacePage";
import { ProcessoWorkspacePage, isProcessoWorkspaceRoute } from "./ui/pages/ProcessoWorkspacePage";
import { ProcessosPage } from "./ui/pages/ProcessosPage";
import { DataTransferPage } from "./ui/pages/DataTransferPage";
import { MeetingMinutesPage } from "./ui/pages/MeetingMinutesPage";
import { MeetingMinuteEditorPage } from "./ui/pages/MeetingMinuteEditorPage";
import { MeetingMinuteDetailPage } from "./ui/pages/MeetingMinuteDetailPage";
import { MeetingMinuteSignPage } from "./ui/pages/MeetingMinuteSignPage";
import { MeetingMinutesPendingPage } from "./ui/pages/MeetingMinutesPendingPage";
import { MySignaturePage } from "./ui/pages/MySignaturePage";
import { DiagramEditorPage } from "./ui/pages/DiagramEditorPage";
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

function AppRoutes({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  const pathname = useTransformometroRouterPath(pathnameFromHost);
  const route = parseTransformometroPath(pathname);
  const transitionKey = buildTransformometroTransitionKey(pathname);

  useDelpiPortalBridge(pathname);

  const onNavigate = useGuardedNavigate(navigateTransformometro);

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
  } else if (route.view === "atas") {
    page = <MeetingMinutesPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />;
  } else if (route.view === "ataNew" || route.view === "ataEdit") {
    page = <MeetingMinuteEditorPage getAccessToken={getAccessToken} ataId={route.ataId} onNavigate={onNavigate} />;
  } else if (route.view === "ata" && route.ataId) {
    page = (
      <MeetingMinuteDetailPage
        getAccessToken={getAccessToken}
        ataId={route.ataId}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  } else if (route.view === "ataSign" && route.ataId) {
    page = <MeetingMinuteSignPage getAccessToken={getAccessToken} ataId={route.ataId} onNavigate={onNavigate} />;
  } else if (route.view === "atasPending") {
    page = <MeetingMinutesPendingPage getAccessToken={getAccessToken} onNavigate={onNavigate} />;
  } else if (route.view === "minhaAssinatura") {
    page = <MySignaturePage getAccessToken={getAccessToken} onNavigate={onNavigate} />;
  } else if (route.view === "processoDiagramaEdit" && route.processoId) {
    page = (
      <DiagramEditorPage
        kind="processo"
        processoId={route.processoId}
        getAccessToken={getAccessToken}
        onNavigate={onNavigate}
      />
    );
  } else if (
    route.view === "instanciaDiagramaEdit" &&
    route.processoId &&
    route.instanciaId
  ) {
    page = (
      <DiagramEditorPage
        kind="instancia"
        processoId={route.processoId}
        instanciaId={route.instanciaId}
        getAccessToken={getAccessToken}
        onNavigate={onNavigate}
      />
    );
  } else if (
    route.view === "revisaoDiagramaEdit" &&
    route.processoId &&
    route.instanciaId &&
    route.revisaoId
  ) {
    page = (
      <DiagramEditorPage
        kind="revisao"
        processoId={route.processoId}
        instanciaId={route.instanciaId}
        revisaoId={route.revisaoId}
        getAccessToken={getAccessToken}
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
              : buildProcessoPath(id),
          )
        }
      />
    );
  } else {
    page = (
      <DashboardPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  }

  return <PageTransition transitionKey={transitionKey}>{page}</PageTransition>;
}

export default function App(props: AppProps) {
  return (
    <ConfirmDialogProvider>
      <UnsavedChangesGuardProvider>
        <FloatingNoticeProvider>
          <AppRoutes {...props} />
        </FloatingNoticeProvider>
      </UnsavedChangesGuardProvider>
    </ConfirmDialogProvider>
  );
}
