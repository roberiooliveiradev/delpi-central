import { ActionButton, DataTable, EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getOpenOrders } from "../../api/openOrdersApi";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialLoadingCard,
  CommercialTitleWithHelp,
} from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import type { SellerPortfolio } from "../../types/portfolio";
import { formatCurrency } from "../../utils/format";

type TeamRow = {
  id: string;
  name: string;
  customers: number;
  lines: number;
  openValue: number;
  error?: string | null;
};

const TEAM_FETCH_CAP = 20;

type AnalyticsTeamPageProps = {
  basePath: string;
};

export function AnalyticsTeamPage({ basePath }: AnalyticsTeamPageProps) {
  const {
    sellers,
    loading: scopeLoading,
    reloadScope,
    canManagePortfolios,
    isAdmin,
  } = usePortfolioScope();
  const canOpenAdmin = canManagePortfolios || isAdmin;
  const [rows, setRows] = useState<TeamRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const activeSellers = useMemo(
    () => sellers.filter((seller) => seller.active).slice(0, TEAM_FETCH_CAP),
    [sellers],
  );

  useEffect(() => {
    if (scopeLoading) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    void Promise.all(
      activeSellers.map(async (seller: SellerPortfolio) => {
        try {
          const data = await getOpenOrders(controller.signal, { sellerId: seller.id });
          const items = data.items ?? [];
          return {
            id: seller.id,
            name: seller.display_name,
            customers: seller.customer_count,
            lines: data.summary?.total_linhas ?? items.length,
            openValue: data.summary?.valor_total_aberto ?? 0,
            error: null,
          } satisfies TeamRow;
        } catch (err) {
          return {
            id: seller.id,
            name: seller.display_name,
            customers: seller.customer_count,
            lines: 0,
            openValue: 0,
            error: err instanceof Error ? err.message : "Falha ao carregar pedidos",
          } satisfies TeamRow;
        }
      }),
    )
      .then((next) => {
        if (!controller.signal.aborted) setRows(next);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar equipe.");
        setRows([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [activeSellers, scopeLoading, reloadKey]);

  const columns: DataTableColumn<TeamRow>[] = [
    { key: "name", header: "Vendedor", render: (row) => row.name },
    {
      key: "customers",
      header: "Clientes",
      render: (row) => row.customers.toLocaleString("pt-BR"),
    },
    {
      key: "lines",
      header: "Linhas abertas",
      render: (row) =>
        row.error ? (
          <span title={row.error}>—</span>
        ) : (
          row.lines.toLocaleString("pt-BR")
        ),
    },
    {
      key: "openValue",
      header: "Valor aberto",
      render: (row) => (row.error ? "—" : formatCurrency(row.openValue)),
    },
    {
      key: "actions",
      header: "",
      render: (row) => (
        <ActionButton
          variant="ghost"
          onClick={() =>
            navigatePluginView("open_orders", {
              basePath,
              search: `?seller_id=${encodeURIComponent(row.id)}`,
            })
          }
        >
          Pedidos
        </ActionButton>
      ),
    },
  ];

  return (
    <section className="cm-page-stack">
      <header className="cm-page-header-row">
        <CommercialTitleWithHelp
          title={ANALYTICS_CONTENT.equipe.title}
          hint={ANALYTICS_CONTENT.equipe.subtitle}
        />
        <ActionButton
          variant="ghost"
          onClick={() => {
            reloadScope();
            setReloadKey((v) => v + 1);
          }}
        >
          <RefreshCw size={16} aria-hidden="true" /> Atualizar
        </ActionButton>
      </header>

      <SectionCard
        title="Carteiras ativas"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loading || scopeLoading ? (
          <CommercialLoadingCard title="Carregando equipe…" variant="panel" />
        ) : null}
        {error ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
        ) : null}
        {!loading && !scopeLoading && rows.length === 0 ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultTitle="Nenhuma carteira ativa"
            defaultMessage={
              canOpenAdmin
                ? "Cadastre vendedores em Administração para ver a equipe."
                : "Nenhuma carteira ativa no momento. Peça ao gerente para cadastrar carteiras."
            }
          >
            {canOpenAdmin ? (
              <ActionButton
                variant="primary"
                onClick={() => navigatePluginView("administration", { basePath })}
              >
                Abrir Administração
              </ActionButton>
            ) : null}
          </EmptyState>
        ) : null}
        {!loading && rows.length > 0 ? (
          <DataTable
            rows={rows}
            columns={columns}
            rowKey={(row) => row.id}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        ) : null}
      </SectionCard>
    </section>
  );
}
