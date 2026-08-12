import { HelpTooltip, SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialDataListToolbar,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialViewTransition,
  UI_PREFIX,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import type { SellerPortfolio } from "../../types/portfolio";
import type { SellerPortfoliosAxis } from "../../utils/sellerPortfoliosDeepLink";

type OrgPersonNode = {
  userId: string;
  portfolios: SellerPortfolio[];
};

type OrgPortfolioNode = {
  portfolio: SellerPortfolio;
  memberIds: string[];
};

type SellerPortfoliosOrgViewProps = {
  portfolios: SellerPortfolio[];
  axis: SellerPortfoliosAxis;
  loading: boolean;
  emptyTitle: string;
  emptyMessage: string;
  onAxisChange: (axis: SellerPortfoliosAxis) => void;
  onOpenPortfolio: (portfolio: SellerPortfolio) => void;
  onCreate: () => void;
  directoryLabelFor: (userId: string, fallback?: string | null) => string;
};

function resolveMemberIds(portfolio: SellerPortfolio): string[] {
  const fromMembers = (portfolio.members ?? [])
    .map((member) => member.user_id.trim())
    .filter(Boolean);
  if (fromMembers.length > 0) return [...new Set(fromMembers)];
  const owner = (portfolio.owner_user_id ?? portfolio.user_id).trim();
  return owner ? [owner] : [];
}

function buildPortfolioNodes(portfolios: SellerPortfolio[]): OrgPortfolioNode[] {
  return portfolios.map((portfolio) => ({
    portfolio,
    memberIds: resolveMemberIds(portfolio),
  }));
}

function buildPersonNodes(portfolios: SellerPortfolio[]): OrgPersonNode[] {
  const byUser = new Map<string, SellerPortfolio[]>();
  for (const portfolio of portfolios) {
    for (const userId of resolveMemberIds(portfolio)) {
      const current = byUser.get(userId) ?? [];
      current.push(portfolio);
      byUser.set(userId, current);
    }
  }
  return [...byUser.entries()]
    .map(([userId, items]) => ({ userId, portfolios: items }))
    .sort((a, b) => a.userId.localeCompare(b.userId));
}

export function SellerPortfoliosOrgView({
  portfolios,
  axis,
  loading,
  emptyTitle,
  emptyMessage,
  onAxisChange,
  onOpenPortfolio,
  onCreate,
  directoryLabelFor,
}: SellerPortfoliosOrgViewProps) {
  const portfolioNodes = buildPortfolioNodes(portfolios);
  const personNodes = buildPersonNodes(portfolios);

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
          ) : axis === "portfolio" ? (
            <ul className="cm-portfolios-org-tree" aria-label="Organização por carteira">
              {portfolioNodes.map(({ portfolio, memberIds }) => (
                <li key={portfolio.id} className="cm-portfolios-org-tree__node">
                  <CommercialActionButton
                    variant="ghost"
                    onClick={() => onOpenPortfolio(portfolio)}
                    aria-label={`${CM_HELP.sellerPortfolios.cardOpenHint}: ${portfolio.display_name}`}
                  >
                    {portfolio.display_name}
                    {portfolio.active ? "" : " (inativa)"}
                  </CommercialActionButton>
                  {memberIds.length === 0 ? (
                    <p className="cm-portfolios-org-tree__empty">Sem usuários vinculados.</p>
                  ) : (
                    <ul className="cm-portfolios-org-tree__children">
                      {memberIds.map((userId) => (
                        <li key={userId}>{directoryLabelFor(userId, portfolio.display_name)}</li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <ul className="cm-portfolios-org-tree" aria-label="Organização por pessoa">
              {personNodes.map(({ userId, portfolios: personPortfolios }) => (
                <li key={userId} className="cm-portfolios-org-tree__node">
                  <span className="cm-portfolios-org-tree__person">
                    {directoryLabelFor(userId)}
                  </span>
                  <ul className="cm-portfolios-org-tree__children">
                    {personPortfolios.map((portfolio) => (
                      <li key={portfolio.id}>
                        <CommercialActionButton
                          variant="ghost"
                          onClick={() => onOpenPortfolio(portfolio)}
                          aria-label={`${CM_HELP.sellerPortfolios.cardOpenHint}: ${portfolio.display_name}`}
                        >
                          {portfolio.display_name}
                          {portfolio.active ? "" : " (inativa)"}
                        </CommercialActionButton>
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}
        </CommercialViewTransition>
      ) : null}
    </CommercialSectionCard>
  );
}
