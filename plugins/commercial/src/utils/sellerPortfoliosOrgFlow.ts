import type {
  OrgMembershipFlowModelEdge,
  OrgMembershipFlowModelNode,
} from "@delpi/plugin-ui/index";

import type {
  PersonLoadItem,
  PortfolioLoadItem,
  SellerPortfolio,
} from "../types/portfolio";
import type { SellerPortfoliosAxis } from "./sellerPortfoliosDeepLink";
import {
  formatPersonLoadSnippet,
  formatPortfolioLoadSnippet,
  resolvePortfolioLoad,
} from "./portfolioLoad";

export function resolveSellerPortfolioMemberIds(portfolio: SellerPortfolio): string[] {
  const fromMembers = (portfolio.members ?? [])
    .map((member) => member.user_id.trim())
    .filter(Boolean);
  if (fromMembers.length > 0) return [...new Set(fromMembers)];
  const owner = (portfolio.owner_user_id ?? portfolio.user_id).trim();
  return owner ? [owner] : [];
}

function portfolioLoadSnippet(
  portfolio: SellerPortfolio,
  loadByPortfolioId?: ReadonlyMap<string, PortfolioLoadItem>,
): string {
  const load =
    loadByPortfolioId?.get(portfolio.id) ??
    resolvePortfolioLoad(null, portfolio.id, {
      customer_count: portfolio.customer_count,
      member_count:
        portfolio.member_count ??
        (portfolio.members?.length ? portfolio.members.length : 1),
    });
  return formatPortfolioLoadSnippet(load);
}

export type SellerPortfoliosOrgFlowModel = {
  nodes: OrgMembershipFlowModelNode[];
  edges: OrgMembershipFlowModelEdge[];
};

export function buildSellerPortfoliosOrgFlowModel(input: {
  portfolios: readonly SellerPortfolio[];
  axis: SellerPortfoliosAxis;
  loadByPortfolioId?: ReadonlyMap<string, PortfolioLoadItem>;
  loadByPersonId?: ReadonlyMap<string, PersonLoadItem>;
  directoryLabelFor: (userId: string, fallback?: string | null) => string;
}): SellerPortfoliosOrgFlowModel {
  const {
    portfolios,
    axis,
    loadByPortfolioId,
    loadByPersonId,
    directoryLabelFor,
  } = input;

  if (axis === "portfolio") {
    const nodes: OrgMembershipFlowModelNode[] = [];
    const edges: OrgMembershipFlowModelEdge[] = [];
    for (const portfolio of portfolios) {
      const portfolioNodeId = `portfolio:${portfolio.id}`;
      nodes.push({
        id: portfolioNodeId,
        kind: "portfolio",
        entityId: portfolio.id,
        title: `${portfolio.display_name}${portfolio.active ? "" : " (inativa)"}`,
        subtitle: portfolioLoadSnippet(portfolio, loadByPortfolioId),
        tone: portfolio.active ? "neutral" : "muted",
      });
      for (const userId of resolveSellerPortfolioMemberIds(portfolio)) {
        const personNodeId = `person:${userId}`;
        if (!nodes.some((node) => node.id === personNodeId)) {
          nodes.push({
            id: personNodeId,
            kind: "person",
            entityId: userId,
            title: directoryLabelFor(userId, portfolio.display_name),
          });
        }
        edges.push({
          id: `edge:${portfolio.id}:${userId}`,
          source: portfolioNodeId,
          target: personNodeId,
        });
      }
    }
    return { nodes, edges };
  }

  const byUser = new Map<string, SellerPortfolio[]>();
  for (const portfolio of portfolios) {
    for (const userId of resolveSellerPortfolioMemberIds(portfolio)) {
      const current = byUser.get(userId) ?? [];
      current.push(portfolio);
      byUser.set(userId, current);
    }
  }

  const nodes: OrgMembershipFlowModelNode[] = [];
  const edges: OrgMembershipFlowModelEdge[] = [];
  for (const [userId, personPortfolios] of [...byUser.entries()].sort((a, b) =>
    a[0].localeCompare(b[0]),
  )) {
    const personNodeId = `person:${userId}`;
    const personLoad = loadByPersonId?.get(userId);
    const subtitle = personLoad
      ? formatPersonLoadSnippet(personLoad)
      : formatPersonLoadSnippet({
          customer_count: personPortfolios.reduce(
            (sum, item) => sum + (item.customer_count ?? 0),
            0,
          ),
          portfolio_count: personPortfolios.length,
          open_value: null,
          attention_count: null,
        });
    nodes.push({
      id: personNodeId,
      kind: "person",
      entityId: userId,
      title: directoryLabelFor(userId),
      subtitle,
    });
    for (const portfolio of personPortfolios) {
      const portfolioNodeId = `portfolio:${portfolio.id}`;
      if (!nodes.some((node) => node.id === portfolioNodeId)) {
        nodes.push({
          id: portfolioNodeId,
          kind: "portfolio",
          entityId: portfolio.id,
          title: `${portfolio.display_name}${portfolio.active ? "" : " (inativa)"}`,
          subtitle: portfolioLoadSnippet(portfolio, loadByPortfolioId),
          tone: portfolio.active ? "neutral" : "muted",
        });
      }
      edges.push({
        id: `edge:${userId}:${portfolio.id}`,
        source: personNodeId,
        target: portfolioNodeId,
      });
    }
  }
  return { nodes, edges };
}
