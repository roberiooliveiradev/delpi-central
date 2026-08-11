import {
  CommercialInteractiveDataCard,
  CommercialStatusBadge,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import type { SellerPortfolio } from "../../types/portfolio";

type SellerPortfolioListCardProps = {
  portfolio: SellerPortfolio;
  userLabel: string;
  onSelect: (portfolio: SellerPortfolio) => void;
};

export function SellerPortfolioListCard({
  portfolio,
  userLabel,
  onSelect,
}: SellerPortfolioListCardProps) {
  const customerLabel =
    portfolio.customer_count === 1
      ? "1 cliente"
      : `${portfolio.customer_count.toLocaleString("pt-BR")} clientes`;

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
          value: portfolio.display_name,
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
