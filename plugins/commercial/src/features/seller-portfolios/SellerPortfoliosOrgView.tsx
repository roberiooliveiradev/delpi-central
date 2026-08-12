import { useMemo } from "react";
import { HelpTooltip, SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialDataListToolbar,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialOrgMembershipFlow,
  CommercialSectionCard,
  CommercialViewTransition,
  UI_PREFIX,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import type {
  PersonLoadItem,
  PortfolioLoadItem,
  SellerPortfolio,
} from "../../types/portfolio";
import type { SellerPortfoliosAxis } from "../../utils/sellerPortfoliosDeepLink";
import { buildSellerPortfoliosOrgFlowModel } from "../../utils/sellerPortfoliosOrgFlow";

type SellerPortfoliosOrgViewProps = {
  portfolios: SellerPortfolio[];
  axis: SellerPortfoliosAxis;
  loading: boolean;
  emptyTitle: string;
  emptyMessage: string;
  loadByPortfolioId?: ReadonlyMap<string, PortfolioLoadItem>;
  loadByPersonId?: ReadonlyMap<string, PersonLoadItem>;
  onAxisChange: (axis: SellerPortfoliosAxis) => void;
  onOpenPortfolio: (portfolio: SellerPortfolio) => void;
  onCreate: () => void;
  directoryLabelFor: (userId: string, fallback?: string | null) => string;
};

export function SellerPortfoliosOrgView({
  portfolios,
  axis,
  loading,
  emptyTitle,
  emptyMessage,
  loadByPortfolioId,
  loadByPersonId,
  onAxisChange,
  onOpenPortfolio,
  onCreate,
  directoryLabelFor,
}: SellerPortfoliosOrgViewProps) {
  const flowModel = useMemo(
    () =>
      buildSellerPortfoliosOrgFlowModel({
        portfolios,
        axis,
        loadByPortfolioId,
        loadByPersonId,
        directoryLabelFor,
      }),
    [portfolios, axis, loadByPortfolioId, loadByPersonId, directoryLabelFor],
  );

  const portfolioById = useMemo(() => {
    const map = new Map<string, SellerPortfolio>();
    for (const portfolio of portfolios) map.set(portfolio.id, portfolio);
    return map;
  }, [portfolios]);

  return (
    <CommercialSectionCard
      title="Organização"
      subtitle="Relação entre carteiras e usuários com acesso ao Portal Comercial."
      hint={CM_HELP.sellerPortfolios.shellViewToggle}
    >
      <CommercialDataListToolbar
        leading={
          <HelpTooltip
            content={CM_HELP.sellerPortfolios.orgAxisToggle}
            ariaLabel="Ajuda: eixo da organização"
            wrap
            placement="bottom"
          >
            <SegmentToggle
              prefix={UI_PREFIX}
              size="sm"
              ariaLabel="Eixo da organização"
              idPrefix="seller-portfolios-org-axis"
              value={axis}
              onChange={(next) => onAxisChange(next as SellerPortfoliosAxis)}
              options={[
                { value: "portfolio", label: "Por carteira" },
                { value: "person", label: "Por pessoa" },
              ]}
            />
          </HelpTooltip>
        }
      />

      {loading ? <CommercialLoadingCard title="Carregando organização" variant="panel" /> : null}

      {!loading ? (
        <CommercialViewTransition
          transitionKey={`org-${axis}-${portfolios.length}`}
          tone="panel"
        >
          {portfolios.length === 0 ? (
            <CommercialEmptyState title={emptyTitle} message={emptyMessage}>
              <CommercialActionButton variant="primary" onClick={onCreate}>
                Nova carteira
              </CommercialActionButton>
            </CommercialEmptyState>
          ) : (
            <CommercialOrgMembershipFlow
              nodes={flowModel.nodes}
              edges={flowModel.edges}
              aria-label={
                axis === "portfolio"
                  ? "Organização por carteira"
                  : "Organização por pessoa"
              }
              emptyMessage="Sem vínculos de carteira e usuários para exibir."
              onNodeClick={(payload) => {
                if (payload.kind !== "portfolio") return;
                const portfolio = portfolioById.get(payload.entityId);
                if (portfolio) onOpenPortfolio(portfolio);
              }}
            />
          )}
        </CommercialViewTransition>
      ) : null}
    </CommercialSectionCard>
  );
}
