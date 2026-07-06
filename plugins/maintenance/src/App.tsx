import { useMaintenanceRouterPath } from "./hooks/useMaintenanceRouterPath";
import { parseMaintenancePath } from "./utils/routeParser";
import { navigateMaintenance } from "./utils/navigation";
import { PageTransition } from "./components/PageTransition";
import { HomePage } from "./ui/pages/HomePage";
import { MiniAplicadoresPage } from "./ui/pages/MiniAplicadoresPage";
import { ConfiguracaoPage } from "./ui/pages/ConfiguracaoPage";
import { FiliaisPage } from "./ui/pages/FiliaisPage";
import { ManutencaoGeralPage } from "./ui/pages/ManutencaoGeralPage";
import { RelatorioPage } from "./ui/pages/RelatorioPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  /** URL externa declarada em `routes[].entry` do manifesto (portal → `alternateEntry`). */
  alternateEntry?: string;
};

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  alternateEntry,
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
        onNavigate={onNavigate}
      />
    );
  }

  return <PageTransition transitionKey={transitionKey}>{page}</PageTransition>;
}
