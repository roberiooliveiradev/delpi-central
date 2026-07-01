import { configureHttpClient } from "./api/httpClient";
import { CustomerExperiencePage } from "./pages/CustomerExperiencePage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return (
    <div className="dashboard-customer-experience dashboard-page">
      <div className="cx-app-shell">
        <CustomerExperiencePage />
      </div>
    </div>
  );
}
