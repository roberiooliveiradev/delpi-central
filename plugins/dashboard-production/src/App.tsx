import { configureHttpClient } from "./api/httpClient";
import { DashboardProductionPage } from "./pages/DashboardProductionPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return (
    <div className="dp-app-shell">
      <DashboardProductionPage />
    </div>
  );
}
