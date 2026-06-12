import { useMaintenanceRouterPath } from "./hooks/useMaintenanceRouterPath";
import { parseMaintenancePath } from "./utils/routeParser";
import { navigateMaintenance } from "./utils/navigation";
import { HomePage } from "./ui/pages/HomePage";
import { MiniAplicadoresPage } from "./ui/pages/MiniAplicadoresPage";
import { ConfiguracaoPage } from "./ui/pages/ConfiguracaoPage";
import { RelatorioPage } from "./ui/pages/RelatorioPage";

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
        filialScope={route.filialScope}
        onNavigate={onNavigate}
        codigoFerramenta={route.codigoFerramenta}
      />
    );
  }

  if (route.view === "relatorio") {
    return (
      <RelatorioPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        filialScope={route.filialScope}
        onNavigate={onNavigate}
      />
    );
  }

  if (route.view === "configuracao") {
    return (
      <ConfiguracaoPage
        getAccessToken={getAccessToken}
        pathname={pathname}
        filialScope={route.filialScope}
        onNavigate={onNavigate}
      />
    );
  }

  return (
    <HomePage
      getAccessToken={getAccessToken}
      pathname={pathname}
      filialScope={route.filialScope}
      onNavigate={onNavigate}
    />
  );
}
