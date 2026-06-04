import { DashboardPage } from "./ui/pages/DashboardPage";
import { ProcessoDetailPage } from "./ui/pages/ProcessoDetailPage";
import { RecursoDetailPage } from "./ui/pages/RecursoDetailPage";
import { ProcessosPage } from "./ui/pages/ProcessosPage";
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

  if (route.view === "processo" && route.processoId) {
    return (
      <ProcessoDetailPage
        getAccessToken={getAccessToken}
        processoId={route.processoId}
        revisaoId={route.revisaoId ?? null}
        pathname={pathname}
        onNavigate={onNavigate}
        onRevisaoChange={(revisaoId) =>
          onNavigate(buildProcessoPath(route.processoId!, revisaoId))
        }
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
        onOpenProcesso={(id) => onNavigate(buildProcessoPath(id))}
      />
    );
  }

  return (
    <DashboardPage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
  );
}
