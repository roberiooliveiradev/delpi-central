import { configureHttpClient } from "./api/httpClient";
import { DashboardLmpsPage } from "./pages/DashboardLmpsPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return <DashboardLmpsPage />;
}