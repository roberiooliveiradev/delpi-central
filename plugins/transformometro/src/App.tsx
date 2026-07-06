import type { ReactNode } from "react";

import { PageTransition } from "./components/PageTransition";
import { DashboardPage } from "./ui/pages/DashboardPage";
import { FilialDetailPage } from "./ui/pages/FilialDetailPage";
import { InstanciaDetailPage } from "./ui/pages/InstanciaDetailPage";
import { ProcessoDetailPage } from "./ui/pages/ProcessoDetailPage";
import { RevisaoDetailPage } from "./ui/pages/RevisaoDetailPage";
import { RecursoDetailPage } from "./ui/pages/RecursoDetailPage";
import { SetorDetailPage } from "./ui/pages/SetorDetailPage";
import { ProcessosPage } from "./ui/pages/ProcessosPage";
import { SetoresPage } from "./ui/pages/SetoresPage";
import { FiliaisPage } from "./ui/pages/FiliaisPage";
import { RecursosPage } from "./ui/pages/RecursosPage";
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
  } else if (route.view === "recurso" && route.recursoId) {
    page = (
      <RecursoDetailPage
        getAccessToken={getAccessToken}
        recursoId={route.recursoId}
        pathname={pathname}
        onNavigate={onNavigate}
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.recursos)}
      />
    );
  } else if (route.view === "filial" && route.filialId) {
    page = (
      <FilialDetailPage
        getAccessToken={getAccessToken}
        filialId={route.filialId}
        pathname={pathname}
        onNavigate={onNavigate}
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.filiais)}
      />
    );
  } else if (route.view === "setor" && route.setorId) {
    page = (
      <SetorDetailPage
        getAccessToken={getAccessToken}
        setorId={route.setorId}
        pathname={pathname}
        onNavigate={onNavigate}
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.setores)}
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
  } else if (route.view === "recursos") {
    page = (
      <RecursosPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  } else if (route.view === "setores") {
    page = (
      <SetoresPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  } else if (route.view === "filiais") {
    page = (
      <FiliaisPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  } else if (route.view === "revisao" && route.processoId && route.revisaoId) {
    page = (
      <RevisaoDetailPage
        getAccessToken={getAccessToken}
        processoId={route.processoId}
        instanciaId={route.instanciaId ?? ""}
        revisaoId={route.revisaoId}
        legacyRevisaoPath={route.legacyRevisaoPath}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  } else if (route.view === "instancia" && route.processoId && route.instanciaId) {
    page = (
      <InstanciaDetailPage
        getAccessToken={getAccessToken}
        processoId={route.processoId}
        instanciaId={route.instanciaId}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  } else if (route.view === "processo" && route.processoId) {
    page = (
      <ProcessoDetailPage
        getAccessToken={getAccessToken}
        processoId={route.processoId}
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

  return <PageTransition transitionKey={transitionKey}>{page}</PageTransition>;
}
