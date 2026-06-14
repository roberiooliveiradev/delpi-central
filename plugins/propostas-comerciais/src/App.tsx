import { configureHttpClient } from "./api/httpClient";
import { PropostaComercialDetailPage } from "./pages/PropostaComercialDetailPage";
import { PropostasComerciaisListPage } from "./pages/PropostasComerciaisListPage";
import { usePropostasComerciaisRouterPath } from "./hooks/usePropostasComerciaisRouterPath";
import { parsePropostasComerciaisPath } from "./utils/route";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  basePath?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = usePropostasComerciaisRouterPath(pathnameFromHost);
  const route = parsePropostasComerciaisPath(pathname);

  return (
    <div className="dashboard-propostas-comerciais dashboard-page">
      <div className="pc-app-shell">
        {route.view === "detail" && route.propostaInterna ? (
          <PropostaComercialDetailPage propostaInterna={route.propostaInterna} />
        ) : (
          <PropostasComerciaisListPage />
        )}
      </div>
    </div>
  );
}
