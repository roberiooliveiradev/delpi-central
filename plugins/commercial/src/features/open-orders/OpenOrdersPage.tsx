import { useEffect, useMemo, useState } from "react";
import {
  DataTable,
  EmptyState,
  SectionCard,
  StateBanner,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import { getOpenOrders, resolveOrderStatus } from "../../api/openOrdersApi";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
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

export function OpenOrdersPage() {
  const { myPortfolio } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<OpenOrderItem[]>([]);
  const [portfolioMessage, setPortfolioMessage] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getOpenOrders(controller.signal, { sellerId: myPortfolio?.id ?? null })
      .then((data) => {
        setItems(data.items ?? []);
        setPortfolioMessage(data.portfolio?.message ?? null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao carregar pedidos.");
        setItems([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [myPortfolio?.id]);

  const columns = useMemo<DataTableColumn<OpenOrderItem>[]>(
    () => [
      { key: "pedido", header: "Pedido", render: (row) => row.pedido },
      { key: "cliente", header: "Cliente", render: (row) => row.nome_cliente },
      { key: "produto", header: "Produto", render: (row) => row.produto },
      {
        key: "qty",
        header: "Qtd.",
        align: "right",
        render: (row) => (row.saldo ?? row.quantidade).toLocaleString("pt-BR"),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => resolveOrderStatus(row),
      },
      { key: "filial", header: "Filial", render: (row) => row.filial },
    ],
    [],
  );

  return (
    <section className="cm-page-stack">
      {portfolioMessage ? (
        <StateBanner variant="default" classNames={cmStateBannerClassNames}>
          {portfolioMessage}
        </StateBanner>
      ) : null}

      <SectionCard
        title="Pedidos em aberto"
        subtitle={`${items.length} linha(s) no escopo atual`}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loading ? (
          <CommercialLoadingCard title="Carregando pedidos" variant="panel" />
        ) : error ? (
          <StateBanner variant="error" classNames={cmStateBannerClassNames}>
            {error}
          </StateBanner>
        ) : items.length === 0 ? (
          <EmptyState
            title="Nenhum pedido em aberto"
            message="Não há linhas para o escopo atual."
            defaultMessage="Não há linhas para o escopo atual."
            classNames={cmEmptyStateClassNames}
          />
        ) : (
          <DataTable
            rows={items}
            columns={columns}
            rowKey={(row: OpenOrderItem, index: number) => `${row.pedido}-${row.produto}-${index}`}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        )}
      </SectionCard>
    </section>
  );
}
