import { configureHttpClient } from "./api/httpClient";
import { DashboardQualityPage } from "./pages/DashboardQualityPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return <DashboardQualityPage />;
}
