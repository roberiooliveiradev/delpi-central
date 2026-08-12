import {
  CommercialActionButton,
  CommercialStatusBadge,
  PORTFOLIOS_LAYOUT_STORAGE_KEY,
  type DataTableColumn,
} from "../../app/commercialUi";
import { CommercialDataTableSection } from "../../app/dataTableUi";
import { CM_HELP } from "../../content/helpTooltips";
import { PORTFOLIO_COVERAGE_CONTENT } from "../../content/portfolioCoverageContent";
import { PORTFOLIO_LOAD_CONTENT } from "../../content/portfolioLoadContent";
import type { PortfolioLoadItem, SellerPortfolio } from "../../types/portfolio";
import { formatCompactOpenValue } from "../../utils/portfolioLoad";
import { SellerPortfolioListCard } from "./SellerPortfolioListCard";

type SellerPortfoliosListProps = {
  portfolios: SellerPortfolio[];
  overlappingPortfolioIds?: ReadonlySet<string>;
  loadByPortfolioId?: ReadonlyMap<string, PortfolioLoadItem>;
  loading: boolean;
  emptyTitle: string;
  emptyMessage: string;
  onSelect: (portfolio: SellerPortfolio) => void;
  onCreate: () => void;
  directoryLabelFor: (userId: string, fallback?: string | null) => string;
};

function memberCountFor(
  portfolio: SellerPortfolio,
  load: PortfolioLoadItem | undefined,
): number {
  if (load?.member_count != null) return load.member_count;
  if (portfolio.member_count != null) return portfolio.member_count;
  const fromMembers = portfolio.members?.length ?? 0;
  return fromMembers > 0 ? fromMembers : 1;
}

export function SellerPortfoliosList({
  portfolios,
  overlappingPortfolioIds,
  loadByPortfolioId,
  loading,
  emptyTitle,
  emptyMessage,
  onSelect,
  onCreate,
  directoryLabelFor,
}: SellerPortfoliosListProps) {
  const columns: DataTableColumn<SellerPortfolio>[] = [
    {
      key: "display_name",
      header: "Carteira",
      headerHint: CM_HELP.sellerPortfolios.colDisplayName,
      render: (row) => (
        <span className="cm-row-actions">
          <span>{row.display_name}</span>
          {row.active && overlappingPortfolioIds?.has(row.id) ? (
            <CommercialStatusBadge
              label={PORTFOLIO_COVERAGE_CONTENT.overlappingBadge}
              variant="warning"
            />
          ) : null}
        </span>
      ),
    },
    {
      key: "user_id",
      header: "Responsável",
      headerHint: CM_HELP.sellerPortfolios.colUserId,
      render: (row) =>
        directoryLabelFor(row.owner_user_id ?? row.user_id, row.display_name),
    },
    {
      key: "customer_count",
      header: "Clientes",
      headerHint: CM_HELP.sellerPortfolios.colCustomerCount,
      align: "right",
      render: (row) =>
        (loadByPortfolioId?.get(row.id)?.customer_count ?? row.customer_count).toLocaleString(
          "pt-BR",
        ),
    },
    {
      key: "member_count",
      header: PORTFOLIO_LOAD_CONTENT.colMembers,
      headerHint: CM_HELP.sellerPortfolios.colMemberCount,
      align: "right",
      render: (row) =>
        memberCountFor(row, loadByPortfolioId?.get(row.id)).toLocaleString("pt-BR"),
    },
    {
      key: "open_value",
      header: PORTFOLIO_LOAD_CONTENT.colOpenValue,
      headerHint: CM_HELP.sellerPortfolios.colOpenValue,
      align: "right",
      render: (row) =>
        formatCompactOpenValue(loadByPortfolioId?.get(row.id)?.open_value ?? null),
    },
    {
      key: "attention_count",
      header: PORTFOLIO_LOAD_CONTENT.colAttention,
      headerHint: CM_HELP.sellerPortfolios.colAttentionCount,
      align: "right",
      render: (row) => {
        const count = loadByPortfolioId?.get(row.id)?.attention_count;
        return count == null
          ? PORTFOLIO_LOAD_CONTENT.attentionUnavailable
          : count.toLocaleString("pt-BR");
      },
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
    <CommercialDataTableSection
      title={`Carteiras (${portfolios.length.toLocaleString("pt-BR")})`}
      titleHint={CM_HELP.sellerPortfolios.list}
      hint="Usuários com acesso ao Portal Comercial + nome de exibição."
      columns={columns}
      rows={portfolios}
      rowKey={(row) => row.id}
      loading={loading}
      emptyMessage={`${emptyTitle}. ${emptyMessage}`}
      onRowClick={onSelect}
      columnPreferencesKey="commercial:seller-portfolios:columns:v1"
      fontSizePreferencesKey="commercial:seller-portfolios:table-font-size:v1"
      viewLayoutPreferencesKey={PORTFOLIOS_LAYOUT_STORAGE_KEY}
      renderCard={(portfolio) => (
        <SellerPortfolioListCard
          portfolio={portfolio}
          load={loadByPortfolioId?.get(portfolio.id) ?? null}
          hasOverlappingCustomers={Boolean(
            portfolio.active && overlappingPortfolioIds?.has(portfolio.id),
          )}
          userLabel={directoryLabelFor(
            portfolio.owner_user_id ?? portfolio.user_id,
            portfolio.display_name,
          )}
          onSelect={onSelect}
        />
      )}
      headerActions={
        <CommercialActionButton variant="primary" onClick={onCreate}>
          Nova carteira
        </CommercialActionButton>
      }
      getSearchText={(row) =>
        [
          row.display_name,
          directoryLabelFor(row.owner_user_id ?? row.user_id, row.display_name),
          row.active ? "ativa" : "inativa",
        ].join(" ")
      }
    />
  );
}
