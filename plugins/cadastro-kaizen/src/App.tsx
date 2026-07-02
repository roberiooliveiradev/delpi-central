import { configureHttpClient } from "./api/httpClient";
import { useKaizenRouterPath } from "./hooks/useKaizenRouterPath";
import { CadastroKaizenPage } from "./pages/CadastroKaizenPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const pathname = useKaizenRouterPath(pathnameFromHost);

  return (
    <div className="dashboard-cadastro-kaizen dashboard-page">
      <div className="kz-app-shell">
        <CadastroKaizenPage pathname={pathname} />
      </div>
    </div>
  );
}
