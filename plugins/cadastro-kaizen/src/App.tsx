import { configureHttpClient } from "./api/httpClient";
import { CadastroKaizenPage } from "./pages/CadastroKaizenPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return (
    <div className="dashboard-cadastro-kaizen dashboard-page">
      <div className="kz-app-shell">
        <CadastroKaizenPage pathname={pathname} />
      </div>
    </div>
  );
}
