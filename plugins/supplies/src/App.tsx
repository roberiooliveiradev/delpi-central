import { configureHttpClient } from "./api/httpClient";
import { PluginShell } from "./app/PluginShell";
import { canAccessUserProfile, canAccessView } from "./app/routeAccess";
import {
  normalizeBasePath,
  resolvePluginRoute,
  SUPPLIES_BASE_PATH,
  type PluginView,
} from "./app/pluginRoutes";
import { SuppliesSessionProvider, useSuppliesSession } from "./app/SuppliesSessionContext";
import { usePluginRouterPath } from "./app/usePluginRouterPath";
import { SuppliesLoadingCard, SuppliesStateBanner } from "./app/suppliesUi";
import { ForbiddenPage } from "./pages/ForbiddenPage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { OverviewPage } from "./pages/OverviewPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { UserManualPage } from "./features/help/UserManualPage";
import { OtdAnalyticsPage } from "./features/analytics/OtdAnalyticsPage";
import { DeliveriesPage } from "./features/deliveries/DeliveriesPage";
import { InventoryPage } from "./features/inventory/InventoryPage";
import { MarketIntelligencePage } from "./features/market-intelligence/MarketIntelligencePage";
import { PurchaseOrderDetailPage } from "./features/purchase-orders/PurchaseOrderDetailPage";
import { PurchaseOrdersPage } from "./features/purchase-orders/PurchaseOrdersPage";
import { PurchaseRequestDetailPage } from "./features/purchase-requests/PurchaseRequestDetailPage";
import { PurchaseRequestsPage } from "./features/purchase-requests/PurchaseRequestsPage";
import { ConsumptionAuditPage } from "./features/consumption-audit/ConsumptionAuditPage";
import { SafetyStockDetailPage } from "./features/safety-stock/SafetyStockDetailPage";
import { SafetyStockPage } from "./features/safety-stock/SafetyStockPage";
import { SupplierCreatePage } from "./features/suppliers/SupplierCreatePage";
import { SupplierDetailPage } from "./features/suppliers/SupplierDetailPage";
import { SuppliersPage } from "./features/suppliers/SuppliersPage";
import { UserProfilePage } from "./features/users/UserProfilePage";

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
  products: {
    title: "Produtos",
    description: "Composição 360 entra depois da fundação do shell.",
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
        <SuppliesLoadingCard title="Consultando suas permissões" variant="panel" />
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

  const { view, userId, branch, orderNumber, requestNumber, supplierCode, supplierStore, productCode } =
    route;

  if (view === "not_found") {
    return (
      <PluginShell view={view} basePath={basePath}>
        <NotFoundPage basePath={basePath} />
      </PluginShell>
    );
  }

  if (view === "user_profile") {
    const targetId = userId || "";
    const allowed = canAccessUserProfile(targetId, session);
    return (
      <PluginShell view={allowed ? view : "forbidden"} basePath={basePath}>
        {allowed ? (
          <UserProfilePage basePath={basePath} userId={targetId} />
        ) : (
          <ForbiddenPage basePath={basePath} />
        )}
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
  } else if (view === "analytics_otd") {
    content = <OtdAnalyticsPage basePath={basePath} />;
  } else if (view === "help") {
    content = <UserManualPage basePath={basePath} />;
  } else if (view === "purchase_requests") {
    content = <PurchaseRequestsPage basePath={basePath} />;
  } else if (view === "purchase_request_detail") {
    content = (
      <PurchaseRequestDetailPage
        basePath={basePath}
        branch={branch || ""}
        requestNumber={requestNumber || ""}
      />
    );
  } else if (view === "purchase_orders") {
    content = <PurchaseOrdersPage basePath={basePath} />;
  } else if (view === "purchase_order_detail") {
    content = (
      <PurchaseOrderDetailPage
        basePath={basePath}
        branch={branch || ""}
        orderNumber={orderNumber || ""}
      />
    );
  } else if (view === "suppliers") {
    content = <SuppliersPage basePath={basePath} />;
  } else if (view === "supplier_detail") {
    content = (
      <SupplierDetailPage
        basePath={basePath}
        code={supplierCode || ""}
        store={supplierStore || ""}
      />
    );
  } else if (view === "supplier_create") {
    content = <SupplierCreatePage basePath={basePath} />;
  } else if (view === "deliveries") {
    content = <DeliveriesPage basePath={basePath} />;
  } else if (view === "inventory") {
    content = <InventoryPage basePath={basePath} />;
  } else if (view === "safety_stock") {
    content = <SafetyStockPage basePath={basePath} />;
  } else if (view === "market_intelligence") {
    // PROC-0076: rota acessível por URL e navegação do hub (gate de
    // página reconciliado; permissão efetiva supplies.access).
    content = <MarketIntelligencePage basePath={basePath} />;
  } else if (view === "consumption_audit") {
    content = <ConsumptionAuditPage basePath={basePath} />;
  } else if (view === "safety_stock_detail") {
    content = (
      <SafetyStockDetailPage
        basePath={basePath}
        branch={branch || ""}
        productCode={productCode || ""}
      />
    );
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
