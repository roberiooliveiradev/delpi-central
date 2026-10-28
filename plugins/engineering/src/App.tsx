import { useEffect, useMemo } from "react";

import { configureHttpClient } from "./api/httpClient";
import { EngineeringPluginShell } from "./app/EngineeringPluginShell";
import { openCatalogRoute } from "./app/openCatalogRoute";
import {
  ENGINEERING_BASE_PATH,
  navigateEngineeringView,
  resolveEngineeringRoute,
} from "./app/engineeringRoutes";
import {
  HOME_COPY,
  visibleSections,
  type CatalogRoute,
} from "./content/engineeringRouteCatalog";
import { HelpPage } from "./features/help/HelpPage";
import { HomePage } from "./features/home/HomePage";
import { OverviewPage } from "./features/overview/OverviewPage";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
} from "./ui/engineeringUi";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  search?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

export default function App({
  getAccessToken,
  pathname,
  permissions,
  isSuperadmin,
}: AppProps) {
  useEffect(() => {
    // Getter sempre vem do host — sem fallback local. A limpeza no
    // unmount (bootstrap → resetHttpClient) garante que nenhum callback
    // de sessão anterior fique disponível após a remontagem.
    if (getAccessToken) configureHttpClient(getAccessToken);
  }, [getAccessToken]);

  const basePath = ENGINEERING_BASE_PATH;
  const resolved = resolveEngineeringRoute(pathname, basePath);

  const sections = useMemo(
    () =>
      visibleSections(new Set(permissions ?? []), Boolean(isSuperadmin)),
    [permissions, isSuperadmin],
  );

  const onOpenRoute = (route: CatalogRoute) =>
    openCatalogRoute(route, basePath);

  if (resolved.view === "not_found") {
    return (
      <EngineeringPluginShell
        view="home"
        basePath={basePath}
        sections={sections}
        getAccessToken={getAccessToken}
        onOpenRoute={onOpenRoute}
      >
        <EngineeringEmptyState message={HOME_COPY.notFound.message}>
          <EngineeringActionButton
            variant="primary"
            onClick={() => navigateEngineeringView("home", { basePath })}
          >
            {HOME_COPY.notFound.backHome}
          </EngineeringActionButton>
        </EngineeringEmptyState>
      </EngineeringPluginShell>
    );
  }

  return (
    <EngineeringPluginShell
      view={resolved.view}
      basePath={basePath}
      sections={sections}
      getAccessToken={getAccessToken}
      onOpenRoute={onOpenRoute}
    >
      {resolved.view === "home" ? (
        <HomePage
          basePath={basePath}
          sections={sections}
          getAccessToken={getAccessToken}
          onOpenRoute={onOpenRoute}
        />
      ) : null}
      {resolved.view === "overview" ? (
        <OverviewPage basePath={basePath} />
      ) : null}
      {resolved.view === "help" ? <HelpPage basePath={basePath} /> : null}
    </EngineeringPluginShell>
  );
}
