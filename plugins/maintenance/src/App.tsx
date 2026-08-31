import { useMaintenanceRouterPath } from "./hooks/useMaintenanceRouterPath";
import { parseMaintenancePath } from "./utils/routeParser";
import { navigateMaintenance } from "./utils/navigation";
import type { HostAppRoute } from "./utils/manutencaoGeralFormUrl";
import { PageTransition } from "./components/PageTransition";
import { MaintenancePluginShell } from "./components/MaintenancePluginShell";
import { HomePage } from "./ui/pages/HomePage";
import { MiniAplicadoresPage } from "./ui/pages/MiniAplicadoresPage";
import { ConfiguracaoPage } from "./ui/pages/ConfiguracaoPage";
import { FiliaisPage } from "./ui/pages/FiliaisPage";
import { ManutencaoGeralPage } from "./ui/pages/ManutencaoGeralPage";
import { ProgramasMaquinasPage } from "./ui/pages/ProgramasMaquinasPage";
import { RelatorioPage } from "./ui/pages/RelatorioPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  /** URL externa da rota atual (`routes[].entry` → AppHost). */
  alternateEntry?: string;
  /** Rotas do manifesto vivo (`/me/apps`) — fonte da verdade para Entry / openInNewTab. */
  appRoutes?: HostAppRoute[];
};

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  alternateEntry,
  appRoutes,
}: AppProps) {
  const pathname = useMaintenanceRouterPath(pathnameFromHost);
  const route = parseMaintenancePath(pathname);
  const onNavigate = navigateMaintenance;
  const transitionKey = `${route.view}:${route.codigoFerramenta ?? ""}:${route.filialScope ?? ""}`;

  let page = (
    <HomePage
      getAccessToken={getAccessToken}
      pathname={pathname}
      filialScope={route.filialScope}
      appRoutes={appRoutes}
      onNavigate={onNavigate}
    />
  );

  if (route.view === "mini-aplicadores" || route.view === "mini-aplicador") {
    page = (
      <MiniAplicadoresPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        filialScope={route.filialScope}
        onNavigate={onNavigate}
        codigoFerramenta={route.codigoFerramenta}
      />
    );
  } else if (route.view === "relatorio") {
    page = (
      <RelatorioPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        filialScope={route.filialScope}
        onNavigate={onNavigate}
      />
    );
  } else if (route.view === "configuracao") {
    page = (
      <ConfiguracaoPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        filialScope={route.filialScope}
        onNavigate={onNavigate}
      />
    );
  } else if (route.view === "filiais") {
    page = (
      <FiliaisPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        filialScope={route.filialScope}
        onNavigate={onNavigate}
      />
    );
  } else if (route.view === "manutencao-geral") {
    page = (
      <ManutencaoGeralPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        filialScope={route.filialScope}
        alternateEntry={alternateEntry}
        appRoutes={appRoutes}
        onNavigate={onNavigate}
      />
    );
  } else if (route.view === "programas-maquinas") {
    page = (
      <ProgramasMaquinasPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        filialScope={route.filialScope}
        onNavigate={onNavigate}
      />
    );
  }

  return (
    <MaintenancePluginShell
      routeView={route.view}
      pathname={pathname}
      filialScope={route.filialScope}
      getAccessToken={getAccessToken}
      onNavigate={onNavigate}
    >
      <PageTransition transitionKey={transitionKey}>{page}</PageTransition>
    </MaintenancePluginShell>
  );
}
