import { configureHttpClient } from "./api/httpClient";
import { ActionPlansPage } from "./pages/ActionPlansPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  return (
    <div className="dashboard-quality-action-plans dashboard-page">
      <div className="pac-app-shell">
        <ActionPlansPage pathname={pathname} />
      </div>
    </div>
  );
}
