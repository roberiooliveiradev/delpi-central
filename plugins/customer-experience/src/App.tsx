import { configureHttpClient } from "./api/httpClient";
import { useCxRouterPath } from "./hooks/useCxRouterPath";
import { CustomerExperiencePage } from "./pages/CustomerExperiencePage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const pathname = useCxRouterPath(pathnameFromHost);

  return (
    <div className="dashboard-customer-experience dashboard-page">
      <div className="cx-app-shell">
        <CustomerExperiencePage pathname={pathname} />
      </div>
    </div>
  );
}
