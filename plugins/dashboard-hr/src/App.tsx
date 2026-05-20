import { configureHttpClient } from "./api/httpClient";
import { DashboardHrPage } from "./pages/DashboardHrPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return (
    <div className="dh-app-shell">
      <DashboardHrPage />
    </div>
  );
}
