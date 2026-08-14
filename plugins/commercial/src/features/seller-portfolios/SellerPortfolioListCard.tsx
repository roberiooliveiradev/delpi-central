import {
  CommercialEntityLink,
  CommercialInteractiveDataCard,
  CommercialStatusBadge,
} from "../../app/commercialUi";
import { portfolioLinkTitle } from "../../content/entityLinkHints";
import { CM_HELP } from "../../content/helpTooltips";
import { PORTFOLIO_COVERAGE_CONTENT } from "../../content/portfolioCoverageContent";
import { PORTFOLIO_LOAD_CONTENT } from "../../content/portfolioLoadContent";
import type { PortfolioLoadItem, SellerPortfolio } from "../../types/portfolio";
import {
  formatCompactOpenValue,
  formatMemberCountShort,
} from "../../utils/portfolioLoad";

type SellerPortfolioListCardProps = {
  portfolio: SellerPortfolio;
  userLabel: string;
  hasOverlappingCustomers?: boolean;
  load?: PortfolioLoadItem | null;
  href?: string | null;
  onSelect: (portfolio: SellerPortfolio) => void;
};

function resolveMemberCount(
  portfolio: SellerPortfolio,
  load: PortfolioLoadItem | null | undefined,
): number {
  if (load?.member_count != null) return load.member_count;
  if (portfolio.member_count != null) return portfolio.member_count;
  const fromMembers = portfolio.members?.length ?? 0;
  if (fromMembers > 0) return fromMembers;
  return 1;
}

export function SellerPortfolioListCard({
  portfolio,
  userLabel,
  hasOverlappingCustomers = false,
  load = null,
  href = null,
  onSelect,
}: SellerPortfolioListCardProps) {
  const customerCount = load?.customer_count ?? portfolio.customer_count;
  const memberCount = resolveMemberCount(portfolio, load);
  const openValue = load?.open_value ?? null;
  const attentionCount = load?.attention_count ?? null;

  const customerLabel =
    customerCount === 1
      ? "1 cliente"
      : `${customerCount.toLocaleString("pt-BR")} clientes`;

  return (
    <CommercialInteractiveDataCard
      ariaLabel={`${CM_HELP.sellerPortfolios.cardOpenHint}: ${portfolio.display_name}`}
      onActivate={() => onSelect(portfolio)}
      openHint={CM_HELP.sellerPortfolios.cardOpenHint}
      fields={[
        {
          id: "name",
          label: "Carteira",
          valueTone: "title",
          value: (
            <span className="cm-row-actions">
              {href ? (
                <CommercialEntityLink
                  href={href}
                  title={portfolioLinkTitle(portfolio.display_name)}
                  className="cm-link-button"
                  onNavigate={() => onSelect(portfolio)}
                >
                  {portfolio.display_name}
                </CommercialEntityLink>
              ) : (
                <span>{portfolio.display_name}</span>
              )}
              {hasOverlappingCustomers ? (
                <CommercialStatusBadge
                  label={PORTFOLIO_COVERAGE_CONTENT.overlappingBadge}
                  variant="warning"
                />
              ) : null}
            </span>
          ),
        },
        {
          id: "user",
          label: "Usuário",
          valueTone: "meta",
          value: userLabel,
        },
        {
          id: "customers",
          label: "Clientes",
          valueTone: "value",
          value: customerLabel,
        },
        {
          id: "members",
          label: PORTFOLIO_LOAD_CONTENT.colMembers,
          valueTone: "meta",
          value: formatMemberCountShort(memberCount),
        },
        {
          id: "open_value",
          label: PORTFOLIO_LOAD_CONTENT.colOpenValue,
          valueTone: "meta",
          value: formatCompactOpenValue(openValue),
        },
        {
          id: "attention",
          label: PORTFOLIO_LOAD_CONTENT.colAttention,
          valueTone: "meta",
          value:
            attentionCount == null
              ? PORTFOLIO_LOAD_CONTENT.attentionUnavailable
              : attentionCount.toLocaleString("pt-BR"),
        },
        {
          id: "status",
          label: "Status",
          value: (
            <CommercialStatusBadge
              label={portfolio.active ? "Ativa" : "Inativa"}
              variant={portfolio.active ? "success" : "neutral"}
            />
          ),
        },
      ]}
    />
  );
}
