import { useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  BackLink,
  DataTable,
  EmptyState,
  SectionCard,
  StateBanner,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import {
  enrichPortfolioCustomers,
  fetchCustomerAvatarObjectUrl,
  getMySellerPortfolio,
} from "../../api/commercialPortfolioApi";
import { getOpenOrders, resolveOrderStatus } from "../../api/openOrdersApi";
import { navigatePluginView } from "../../app/pluginNavigation";
import {
  CommercialLoadingCard,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStateBannerClassNames,
} from "../../app/commercialUi";
import type { OpenOrderItem } from "../../types/openOrders";
import { customerKey, formatCurrency, formatDate } from "../../shared/format";

type CustomerDetailPageProps = {
  codigo: string;
  loja: string;
  basePath: string;
};

type CustomerIdentity = {
  name: string;
  city: string | null;
  state: string | null;
  billed12m: number;
  lastPurchaseDate: string | null;
};

export function CustomerDetailPage({ codigo, loja, basePath }: CustomerDetailPageProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [identity, setIdentity] = useState<CustomerIdentity | null>(null);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [orders, setOrders] = useState<OpenOrderItem[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    Promise.all([
      getMySellerPortfolio(controller.signal),
      getOpenOrders(controller.signal),
      enrichPortfolioCustomers(
        [{ customer_code: codigo, customer_store: loja }],
        controller.signal,
      ),
      fetchCustomerAvatarObjectUrl(codigo, loja, controller.signal),
    ])
      .then(([me, openOrders, enriched, avatar]) => {
        const inPortfolio = (me.portfolio?.customers ?? []).some(
          (customer) =>
            customer.customer_code === codigo && customer.customer_store === loja,
        );
        if (!inPortfolio && !me.is_admin) {
          throw new Error("Cliente fora da sua carteira.");
        }

        const enrich = enriched[0];
        const portfolioCustomer = (me.portfolio?.customers ?? []).find(
          (customer) =>
            customer.customer_code === codigo && customer.customer_store === loja,
        );

        setIdentity({
          name:
            portfolioCustomer?.customer_name?.trim() ||
            enrich?.customer_code ||
            codigo,
          city: enrich?.city ?? null,
          state: enrich?.state ?? null,
          billed12m: enrich?.billed_12m ?? 0,
          lastPurchaseDate: enrich?.last_purchase_date ?? null,
        });
        setAvatarUrl(avatar);

        const filtered = (openOrders.items ?? []).filter((item) => {
          const code = (item.codigo_cadastro ?? "").trim();
          const store = (item.loja_cadastro ?? "").trim();
          return code === codigo && store === loja;
        });
        setOrders(filtered);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao carregar cliente.");
        setIdentity(null);
        setOrders([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => {
      controller.abort();
      if (avatarUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(avatarUrl);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [codigo, loja]);

  const columns = useMemo<DataTableColumn<OpenOrderItem>[]>(
    () => [
      { key: "pedido", header: "Pedido", render: (row) => row.pedido },
      { key: "produto", header: "Produto", render: (row) => row.produto },
      {
        key: "qty",
        header: "Qtd.",
        align: "right",
        render: (row) => (row.saldo ?? row.quantidade).toLocaleString("pt-BR"),
      },
      { key: "status", header: "Status", render: (row) => resolveOrderStatus(row) },
      { key: "filial", header: "Filial", render: (row) => row.filial },
    ],
    [],
  );

  return (
    <section className="cm-page-stack">
      <BackLink onClick={() => navigatePluginView("customers", { basePath })}>
        Voltar para carteira
      </BackLink>

      {loading ? (
        <CommercialLoadingCard title="Carregando cliente" variant="panel" />
      ) : error ? (
        <StateBanner variant="error" classNames={cmStateBannerClassNames}>
          {error}
        </StateBanner>
      ) : identity ? (
        <>
          <SectionCard
            title={identity.name}
            subtitle={`${codigo} · loja ${loja}`}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <div className="cm-customer-header">
              {avatarUrl ? (
                <img src={avatarUrl} alt={`Logo do cliente ${identity.name}`} />
              ) : null}
              <div>
                <p>
                  {[identity.city, identity.state].filter(Boolean).join(" / ") || "Localidade não informada"}
                </p>
                <p>Faturado 12m: {formatCurrency(identity.billed12m)}</p>
                <p>Última compra: {formatDate(identity.lastPurchaseDate)}</p>
                <p>Chave: {customerKey(codigo, loja)}</p>
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Pedidos em aberto deste cliente"
            subtitle={`${orders.length} linha(s)`}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            {orders.length === 0 ? (
              <EmptyState
                title="Sem pedidos em aberto"
                message="Não há pedidos em aberto para este cliente."
                defaultMessage="Não há pedidos em aberto para este cliente."
                classNames={cmEmptyStateClassNames}
              />
            ) : (
              <DataTable
                rows={orders}
                columns={columns}
                rowKey={(row: OpenOrderItem, index: number) =>
                  `${row.pedido}-${row.produto}-${index}`
                }
                classNames={cmDataTableClassNames}
                labels={cmDataTableLabels}
                layout="section"
              />
            )}
          </SectionCard>
        </>
      ) : null}

      <ActionButton variant="ghost" onClick={() => navigatePluginView("customers", { basePath })}>
        Voltar
      </ActionButton>
    </section>
  );
}
