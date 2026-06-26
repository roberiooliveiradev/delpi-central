import { configureHttpClient } from "./api/httpClient";
import { ActionPlansPage } from "./pages/ActionPlansPage";
import { usePacRouterPath } from "./hooks/usePacRouterPath";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const pathname = usePacRouterPath(pathnameFromHost);

  return (
    <div className="dashboard-quality-action-plans dashboard-page">
      <div className="pac-app-shell">
        <ActionPlansPage pathname={pathname} />
      </div>
    </div>
  );
}
