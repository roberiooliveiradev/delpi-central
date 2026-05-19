import { configureHttpClient } from "./api/httpClient";
import { DashboardSuppliesPage } from "./pages/DashboardSuppliesPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return (
    <div className="ds-app-shell">
      <DashboardSuppliesPage />
    </div>
  );
}
