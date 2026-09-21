import { configureHelpdeskClient } from "./api/helpdeskApi";
import { HelpdeskPage } from "./pages/HelpdeskPage";
import { parseHelpdeskRoute, useHelpdeskRouterPath } from "./routing/helpdeskRoute";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname: pathnameFromHost }: AppProps) {
  configureHelpdeskClient(() => getAccessToken?.());
  const pathname = useHelpdeskRouterPath(pathnameFromHost);
  const route = parseHelpdeskRoute(pathname);
  return (
    <div className="dashboard-helpdesk dashboard-page">
      <HelpdeskPage route={route} />
    </div>
  );
}
