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

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  const pathname = useTransformometroRouterPath(pathnameFromHost);
  const route = parseTransformometroPath(pathname);

  useDelpiPortalBridge(pathname);

  const onNavigate = navigateTransformometro;

  if (route.view === "dashboard") {
    return (
      <DashboardPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  }

  if (route.view === "recurso" && route.recursoId) {
    return (
      <RecursoDetailPage
        getAccessToken={getAccessToken}
        recursoId={route.recursoId}
        pathname={pathname}
        onNavigate={onNavigate}
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.recursos)}
      />
    );
  }

  if (route.view === "filial" && route.filialId) {
    return (
      <FilialDetailPage
        getAccessToken={getAccessToken}
        filialId={route.filialId}
        pathname={pathname}
        onNavigate={onNavigate}
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.filiais)}
      />
    );
  }

  if (route.view === "setor" && route.setorId) {
    return (
      <SetorDetailPage
        getAccessToken={getAccessToken}
        setorId={route.setorId}
        pathname={pathname}
        onNavigate={onNavigate}
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.setores)}
      />
    );
  }

  if (route.view === "dados") {
    return (
      <DataTransferPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  }

  if (route.view === "recursos") {
    return (
      <RecursosPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  }

  if (route.view === "setores") {
    return (
      <SetoresPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  }

  if (route.view === "filiais") {
    return (
      <FiliaisPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  }

  if (route.view === "revisao" && route.processoId && route.revisaoId) {
    return (
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
  }

  if (route.view === "instancia" && route.processoId && route.instanciaId) {
    return (
      <InstanciaDetailPage
        getAccessToken={getAccessToken}
        processoId={route.processoId}
        instanciaId={route.instanciaId}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  }

  if (route.view === "processo" && route.processoId) {
    return (
      <ProcessoDetailPage
        getAccessToken={getAccessToken}
        processoId={route.processoId}
        pathname={pathname}
        onNavigate={onNavigate}
        onBack={() => onNavigate(TRANSFORMOMETRO_ROUTES.processos)}
      />
    );
  }

  if (route.view === "processos") {
    return (
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
  }

  return (
    <DashboardPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
  );
}
