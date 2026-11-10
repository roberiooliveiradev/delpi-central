import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PluginErrorBoundary } from "@delpi/plugin-ui/index";
import { useState } from "react";

import { ApiError, configureHttpClient } from "./api/httpClient";
import { SHELL_CONTENT, STATE_CONTENT } from "./content/labels";
import { usePluginPathname } from "./app/navigation";
import { PluginShell } from "./app/PluginShell";
import { PortalProvider, usePortal } from "./app/PortalContext";
import { ForbiddenState, LoadingBlock, QueryErrorState } from "./app/QueryStates";
import { normalizeBasePath, resolveRoute } from "./app/routes";
import { ActionPlansPage } from "./features/action-plans/ActionPlansPage";
import { HelpPage } from "./features/help/HelpPage";
import { HomePage } from "./features/home/HomePage";
import { NotFoundPage } from "./features/home/NotFoundPage";
import { ServerDetailPage } from "./features/servers/ServerDetailPage";
import { ServersPage } from "./features/servers/ServersPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  getFreshAccessToken?: () => Promise<string | undefined>;
  pathname?: string;
  basePath?: string;
  search?: string;
  /** Enviados pelo host federado — não autorizam; a BFF decide. */
  permissions?: readonly string[];
  isSuperadmin?: boolean;
};

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 15_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) =>
          !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failureCount < 2,
      },
    },
  });
}

function PortalRoutes({ pathnameFromHost }: { pathnameFromHost?: string }) {
  const { basePath, capabilities, capabilitiesLoading, capabilitiesError, refetchCapabilities } = usePortal();
  const pathname = usePluginPathname(pathnameFromHost);
  const route = resolveRoute(pathname, basePath);

  let content;
  if (capabilitiesLoading) {
    content = <LoadingBlock title="Abrindo o Portal de TI" />;
  } else if (capabilitiesError?.status === 403) {
    content = <ForbiddenState message={STATE_CONTENT.forbiddenPortal} />;
  } else if (capabilitiesError || !capabilities) {
    content = (
      <QueryErrorState
        error={capabilitiesError ?? new ApiError(0, STATE_CONTENT.errorTitle)}
        onRetry={refetchCapabilities}
      />
    );
  } else if (route.view === "home") {
    content = <HomePage />;
  } else if (route.view === "servers") {
    content = capabilities.can_view_servers ? <ServersPage /> : <ForbiddenState />;
  } else if (route.view === "server_detail" && route.serverId) {
    content = capabilities.can_view_servers ? (
      <ServerDetailPage key={route.serverId} serverId={route.serverId} />
    ) : (
      <ForbiddenState />
    );
  } else if (route.view === "action_plans") {
    content = capabilities.can_view_action_plans ? <ActionPlansPage /> : <ForbiddenState />;
  } else if (route.view === "help") {
    content = <HelpPage />;
  } else {
    content = <NotFoundPage />;
  }

  return (
    <PluginShell view={route.view}>
      <PluginErrorBoundary
        prefix="itp"
        labels={SHELL_CONTENT.errorBoundary}
        onError={(error) => console.error("[it-portal] render", error)}
      >
        {content}
      </PluginErrorBoundary>
    </PluginShell>
  );
}

export default function App({ getAccessToken, pathname, basePath }: AppProps) {
  configureHttpClient(getAccessToken ?? (() => undefined));
  const [queryClient] = useState(createQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <PortalProvider basePath={normalizeBasePath(basePath)}>
        <PortalRoutes pathnameFromHost={pathname} />
      </PortalProvider>
    </QueryClientProvider>
  );
}
