import { configureHttpClient } from "./api/httpClient";
import { DashboardEficienciaFabrilPage } from "./pages/DashboardEficienciaFabrilPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return <DashboardEficienciaFabrilPage />;
}
