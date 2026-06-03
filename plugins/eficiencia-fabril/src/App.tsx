import { configureHttpClient } from "./api/httpClient";
import { DashboardEficienciaFabrilPage } from "./pages/DashboardEficienciaFabrilPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return <DashboardEficienciaFabrilPage pathname={pathname} />;
}
