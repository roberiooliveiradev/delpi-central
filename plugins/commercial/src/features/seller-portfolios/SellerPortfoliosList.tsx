import { HelpTooltip, SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialDataCardsGrid,
  CommercialDataListToolbar,
  CommercialDataTable,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialStatusBadge,
  CommercialViewTransition,
  PORTFOLIOS_LAYOUT_STORAGE_KEY,
  UI_PREFIX,
  usePersistedViewLayout,
  type DataTableColumn,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import type { SellerPortfolio } from "../../types/portfolio";
import { SellerPortfolioListCard } from "./SellerPortfolioListCard";

type SellerPortfoliosListProps = {
  portfolios: SellerPortfolio[];
  selectedId: string | null;
  loading: boolean;
  emptyTitle: string;
  emptyMessage: string;
  onSelect: (portfolio: SellerPortfolio) => void;
  onCreate: () => void;
  directoryLabelFor: (userId: string, fallback?: string | null) => string;
};

export function SellerPortfoliosList({
  portfolios,
  selectedId,
  loading,
  emptyTitle,
  emptyMessage,
  onSelect,
  onCreate,
  directoryLabelFor,
}: SellerPortfoliosListProps) {
  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: PORTFOLIOS_LAYOUT_STORAGE_KEY,
  });
  const selectedIndex = portfolios.findIndex((item) => item.id === selectedId);
  const columns: DataTableColumn<SellerPortfolio>[] = [
    {
      key: "display_name",
      header: "Carteira",
      headerHint: CM_HELP.sellerPortfolios.colDisplayName,
      render: (row) => row.display_name,
    },
    {
      key: "user_id",
      header: "Usuário",
      headerHint: CM_HELP.sellerPortfolios.colUserId,
      render: (row) => directoryLabelFor(row.user_id, row.display_name),
    },
    {
      key: "customer_count",
      header: "Clientes",
      headerHint: CM_HELP.sellerPortfolios.colCustomerCount,
      align: "right",
      render: (row) => row.customer_count.toLocaleString("pt-BR"),
    },
    {
      key: "status",
      header: "Status",
      headerHint: CM_HELP.sellerPortfolios.colStatus,
      render: (row) => (
        <CommercialStatusBadge
          label={row.active ? "Ativa" : "Inativa"}
          variant={row.active ? "success" : "neutral"}
        />
      ),
    },
  ];

  return (
    <CommercialSectionCard
      title={`Carteiras (${portfolios.length.toLocaleString("pt-BR")})`}
      subtitle="Usuário Minha Delpi + nome de exibição no portal."
      hint={CM_HELP.sellerPortfolios.list}
    >
      <CommercialDataListToolbar
        leading={
          <HelpTooltip
            content={CM_HELP.sellerPortfolios.layoutToggle}
            ariaLabel="Ajuda: modo Tabela ou Cards"
            wrap
            placement="bottom"
          >
            <SegmentToggle
              prefix={UI_PREFIX}
              size="sm"
              ariaLabel="Modo de visualização"
              idPrefix="seller-portfolios-layout"
              value={layout}
              onChange={setLayout}
              options={[
                { value: "table", label: "Tabela" },
                { value: "cards", label: "Cards" },
              ]}
            />
          </HelpTooltip>
        }
      />

      {loading ? <CommercialLoadingCard title="Carregando carteiras" variant="panel" /> : null}

      {!loading ? (
        <CommercialViewTransition transitionKey={`layout-${layout}-${portfolios.length}`} tone="panel">
          {portfolios.length === 0 ? (
            <CommercialEmptyState title={emptyTitle} message={emptyMessage}>
              <CommercialActionButton variant="primary" onClick={onCreate}>
                Nova carteira
              </CommercialActionButton>
            </CommercialEmptyState>
          ) : layout === "cards" ? (
            <CommercialDataCardsGrid>
              {portfolios.map((portfolio) => (
                <SellerPortfolioListCard
                  key={portfolio.id}
                  portfolio={portfolio}
                  userLabel={directoryLabelFor(portfolio.user_id, portfolio.display_name)}
                  onSelect={onSelect}
                />
              ))}
            </CommercialDataCardsGrid>
          ) : (
            <CommercialDataTable
              rows={portfolios}
              columns={columns}
              rowKey={(row) => row.id}
              layout="section"
              onRowClick={onSelect}
              rowClickRole="button"
              selection={
                selectedIndex >= 0 ? { kind: "row", indices: [selectedIndex] } : null
              }
            />
          )}
        </CommercialViewTransition>
      ) : null}
    </CommercialSectionCard>
  );
}
