import { configureHttpClient } from "./api/httpClient";
import { PluginShell } from "./app/PluginShell";
import { canAccessView } from "./app/routeAccess";
import {
  normalizeBasePath,
  resolvePluginRoute,
  SUPPLIES_BASE_PATH,
  type PluginView,
} from "./app/pluginRoutes";
import { SuppliesSessionProvider, useSuppliesSession } from "./app/SuppliesSessionContext";
import { usePluginRouterPath } from "./app/usePluginRouterPath";
import { SuppliesStateBanner } from "./app/suppliesUi";
import { ForbiddenPage } from "./pages/ForbiddenPage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { OverviewPage } from "./pages/OverviewPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { UserManualPage } from "./features/help/UserManualPage";
import { PurchaseRequestsPage } from "./features/purchase-requests/PurchaseRequestsPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  basePath?: string;
  search?: string;
};

const PLACEHOLDER: Partial<
  Record<PluginView, { title: string; description: string }>
> = {
  my_tasks: {
    title: "Minhas tarefas",
    description: "A fila de acompanhamento será composta nas jornadas seguintes.",
  },
  purchase_orders: {
    title: "Pedidos de compra",
    description: "Composição operacional entra depois da fundação do shell.",
  },
  deliveries: {
    title: "Entregas",
    description: "Composição operacional entra depois da fundação do shell.",
  },
  suppliers: {
    title: "Fornecedores",
    description: "Composição 360 entra depois da fundação do shell.",
  },
  products: {
    title: "Produtos",
    description: "Composição 360 entra depois da fundação do shell.",
  },
  inventory: {
    title: "Estoque",
    description: "Composição operacional entra depois da fundação do shell.",
  },
  safety_stock: {
    title: "Estoque de segurança",
    description: "Deep link legado permanece até paridade.",
  },
  negotiations: {
    title: "Negociações",
    description: "Análise entra com o recorte analítico.",
  },
  indicators: {
    title: "Indicadores",
    description: "Análise entra com o recorte analítico.",
  },
  administration: {
    title: "Administração",
    description: "Mappings e settings entram depois da fundação.",
  },
};

function AppRoutes({
  basePath,
  pathnameFromHost,
}: {
  basePath: string;
  pathnameFromHost?: string;
}) {
  const pathname = usePluginRouterPath(pathnameFromHost, basePath);
  const route = resolvePluginRoute(pathname, basePath);
  const session = useSuppliesSession();

  if (session.loading) {
    return (
      <div className="dashboard-supplies-portal dashboard-page">
        <SuppliesStateBanner>Consultando suas permissões.</SuppliesStateBanner>
      </div>
    );
  }

  if (session.forbidden) {
    return (
      <div className="dashboard-supplies-portal dashboard-page">
        <ForbiddenPage basePath={basePath} />
      </div>
    );
  }

  if (session.error) {
    return (
      <div className="dashboard-supplies-portal dashboard-page">
        <SuppliesStateBanner variant="error">{session.error}</SuppliesStateBanner>
      </div>
    );
  }

  const { view } = route;

  if (view === "not_found") {
    return (
      <PluginShell view={view} basePath={basePath}>
        <NotFoundPage basePath={basePath} />
      </PluginShell>
    );
  }

  if (!canAccessView(view, session.capabilities)) {
    return (
      <PluginShell view="forbidden" basePath={basePath}>
        <ForbiddenPage basePath={basePath} />
      </PluginShell>
    );
  }

  let content = null;
  if (view === "home") {
    content = <HomePage basePath={basePath} />;
  } else if (view === "overview") {
    content = <OverviewPage basePath={basePath} />;
  } else if (view === "help") {
    content = <UserManualPage basePath={basePath} />;
  } else if (view === "purchase_requests") {
    content = <PurchaseRequestsPage basePath={basePath} />;
  } else {
    const placeholder = PLACEHOLDER[view];
    content = placeholder ? (
      <PlaceholderPage
        basePath={basePath}
        title={placeholder.title}
        description={placeholder.description}
      />
    ) : (
      <NotFoundPage basePath={basePath} />
    );
  }

  return (
    <PluginShell view={view} basePath={basePath}>
      {content}
    </PluginShell>
  );
}

export default function App({ getAccessToken, pathname, basePath }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const resolvedBase = normalizeBasePath(basePath ?? SUPPLIES_BASE_PATH);

  return (
    <SuppliesSessionProvider>
      <AppRoutes basePath={resolvedBase} pathnameFromHost={pathname} />
    </SuppliesSessionProvider>
  );
}
