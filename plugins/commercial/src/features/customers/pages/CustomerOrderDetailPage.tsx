import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
} from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useMemo } from "react";

import {
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialMetricCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import {
  resolvePagePathBack,
} from "../../../app/commercialNavigationReturn";
import { navigatePluginPath } from "../../../app/pluginNavigation";
import { buildCustomerDetailPath } from "../../../app/pluginRoutes";
import { usePortfolioScope } from "../../../app/PortfolioScopeContext";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import { useCustomerDetailData } from "../hooks/useCustomerDetailData";
import { CustomerOrderLines } from "../components/CustomerOrderLines";
import { orderSituationLabel } from "../utils/customerOrderAggregation";
import { buildOrderKey } from "../utils/customerIdentity";
import { buildCustomerDetailSearch } from "../utils/customerDetailSection";

type CustomerOrderDetailPageProps = {
  basePath: string;
  codigo: string;
  loja: string;
  branch: string;
  orderNumber: string;
  search?: string;
};

function formatMaxOverdue(days: number): string {
  if (days <= 0) return "—";
  if (days === 1) return "1 dia";
  return `${days.toLocaleString("pt-BR")} dias`;
}

export function CustomerOrderDetailPage({
  basePath,
  codigo,
  loja,
  branch,
  orderNumber,
  search,
}: CustomerOrderDetailPageProps) {
  const { sellerNameByKey, canViewAnalytics } = usePortfolioScope();
  const {
    loading,
    refreshing,
    error,
    ordersError,
    customer,
    orders,
    reload,
  } = useCustomerDetailData(codigo, loja, { sellerNameByKey });

  const orderKey = buildOrderKey(branch, orderNumber);
  const order = useMemo(
    () => orders.find((item) => item.key === orderKey) ?? null,
    [orderKey, orders],
  );

  const accountPath =
    buildCustomerDetailPath(basePath, codigo, loja) ?? `${basePath}/customers`;
  const pedidosHref = `${accountPath}${buildCustomerDetailSearch("pedidos")}`;
  const back = resolvePagePathBack(
    search,
    { href: pedidosHref, label: "Pedidos da conta" },
    basePath,
  );

  const customerName = customer?.nome?.trim() || `${codigo}/${loja}`;

  return (
    <section className="cm-page-stack cm-customer-order-detail">
      <CommercialPagePath
        back={{
          label: back.label,
          href: back.href,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(back.href);
          },
        }}
        items={[
          {
            id: "account",
            label: customerName,
            href: accountPath,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginPath(accountPath);
            },
          },
          {
            id: "orders",
            label: "Pedidos",
            href: pedidosHref,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginPath(pedidosHref);
            },
          },
        ]}
        current={`Pedido ${orderNumber}`}
      />

      <CommercialPageHero
        aria-label={`Pedido ${orderNumber}`}
        eyebrow="Conta"
        title={`Pedido ${orderNumber}`}
        description={
          loading
            ? "Carregando pedido…"
            : `${customerName} · ${formatOperationalUnitCode(branch)}`
        }
        actions={
          <CommercialActionButton
            variant="ghost"
            onClick={() => reload()}
            disabled={loading || refreshing}
          >
            <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />
            Atualizar
          </CommercialActionButton>
        }
      />

      {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}
      {ordersError ? (
        <CommercialStateBanner variant="warning">{ordersError}</CommercialStateBanner>
      ) : null}

      {loading ? <CommercialLoadingCard title="Carregando pedido" /> : null}

      {!loading && !order ? (
        <CommercialStateBanner variant="warning">
          Pedido não encontrado nos abertos desta conta. Ele pode ter sido faturado ou
          fechado.
        </CommercialStateBanner>
      ) : null}

      {!loading && order ? (
        <>
          <div className="cm-nav-row">
            <CommercialStatusBadge
              variant={
                order.situacao === "atrasado"
                  ? "danger"
                  : order.situacao === "parcial"
                    ? "warning"
                    : "neutral"
              }
              label={orderSituationLabel(order.situacao)}
            />
            <CommercialStatusBadge
              variant="info"
              label={`${OPERATIONAL_UNIT_COLUMN_LABEL} ${formatOperationalUnitCode(order.filial)}`}
            />
          </div>

          <div className="cm-user-profile__portfolio-grid">
            <CommercialMetricCard
              label="Valor em aberto"
              value={formatCurrency(order.valorTotalAberto)}
            />
            <CommercialMetricCard
              label="Linhas"
              value={order.quantidadeLinhas.toLocaleString("pt-BR")}
            />
            <CommercialMetricCard
              label="Maior atraso"
              value={formatMaxOverdue(order.maiorAtrasoDias)}
              tone={order.maiorAtrasoDias > 0 ? "danger" : "default"}
            />
            <CommercialMetricCard
              label="Próxima entrega"
              value={
                order.proximaEntrega
                  ? formatDisplayDate(order.proximaEntrega)
                  : "—"
              }
            />
          </div>

          {order.pedidoCliente ? (
            <CommercialSectionCard title="Referência do cliente">
              <p>{order.pedidoCliente}</p>
            </CommercialSectionCard>
          ) : null}

          <CommercialSectionCard title="Produtos">
            <CustomerOrderLines
              lines={order.lines}
              orderKey={order.key}
              basePath={basePath}
              canViewAnalytics={canViewAnalytics}
            />
          </CommercialSectionCard>
        </>
      ) : null}
    </section>
  );
}
