import { configureHttpClient } from "./api/httpClient";
import { ReportsAppShell } from "./layout/ReportsAppShell";
import { CreateDefinitionPage } from "./pages/CreateDefinitionPage";
import { DefinitionDetailPage } from "./pages/DefinitionDetailPage";
import { DefinitionsListPage } from "./pages/DefinitionsListPage";
import { OverviewPage } from "./pages/OverviewPage";
import { resolveReportsRoute } from "./utils/route";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ getAccessToken, pathname }: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const route = resolveReportsRoute(pathname);

  let content = <OverviewPage />;
  if (route.kind === "list") {
    content = <DefinitionsListPage />;
  } else if (route.kind === "create") {
    content = <CreateDefinitionPage />;
  } else if (route.kind === "detail") {
    content = <DefinitionDetailPage definitionId={route.definitionId} />;
  }

  return <ReportsAppShell nav={route.nav}>{content}</ReportsAppShell>;
}
