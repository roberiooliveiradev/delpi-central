import { configureHttpClient } from "./api/httpClient";
import { CanalDenunciaPage } from "./pages/CanalDenunciaPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return <CanalDenunciaPage />;
}
