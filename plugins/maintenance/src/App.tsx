import { useMaintenanceRouterPath } from "./hooks/useMaintenanceRouterPath";
import { parseMaintenancePath } from "./utils/routeParser";
import { navigateMaintenance } from "./utils/navigation";
import { HomePage } from "./ui/pages/HomePage";
import { MiniAplicadoresPage } from "./ui/pages/MiniAplicadoresPage";
import {
  PlaceholderPage,
  ReportIcon,
} from "./ui/pages/PlaceholderPage";
import { ConfiguracaoPage } from "./ui/pages/ConfiguracaoPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  const pathname = useMaintenanceRouterPath(pathnameFromHost);
  const route = parseMaintenancePath(pathname);
  const onNavigate = navigateMaintenance;

  if (route.view === "mini-aplicadores" || route.view === "mini-aplicador") {
    return (
      <MiniAplicadoresPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={onNavigate}
        codigoFerramenta={route.codigoFerramenta}
      />
    );
  }

  if (route.view === "relatorio") {
    return (
      <PlaceholderPage
        title="Relatório preventivo"
        subtitle="Alertas e histórico de golpes entre reposições."
        icon={ReportIcon}
        phase="Fase 2"
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  }

  if (route.view === "configuracao") {
    return (
      <ConfiguracaoPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        onNavigate={onNavigate}
      />
    );
  }

  return (
    <HomePage getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
  );
}
