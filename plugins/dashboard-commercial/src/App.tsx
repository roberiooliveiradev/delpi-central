import { configureHttpClient } from "./api/httpClient";
import { DashboardCommercialPage } from "./pages/DashboardCommercialPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return (
    <div className="dc-app-shell">
      <DashboardCommercialPage />
    </div>
  );
}
