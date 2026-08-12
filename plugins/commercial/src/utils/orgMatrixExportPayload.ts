/**
 * Payload tabular da matriz org (E6.5) — puro, sem I/O.
 */
import { PORTFOLIO_LOAD_CONTENT } from "../content/portfolioLoadContent";
import type { PortfolioLoadItem, SellerPortfolio } from "../types/portfolio";
import { resolvePortfolioLoad } from "./portfolioLoad";

export type OrgMatrixExportPayload = {
  title: string;
  columns: Array<{ key: string; label: string }>;
  rows: Array<Record<string, unknown>>;
};

function resolveMemberIds(portfolio: SellerPortfolio): string[] {
  const fromMembers = (portfolio.members ?? [])
    .map((member) => member.user_id.trim())
    .filter(Boolean);
  if (fromMembers.length > 0) return [...new Set(fromMembers)];
  const owner = (portfolio.owner_user_id ?? portfolio.user_id).trim();
  return owner ? [owner] : [];
}

function memberLabels(
  portfolio: SellerPortfolio,
  directoryLabelFor: (userId: string, fallback?: string | null) => string,
): string {
  const ids = resolveMemberIds(portfolio);
  if (ids.length === 0) return "";
  return ids.map((userId) => directoryLabelFor(userId, portfolio.display_name)).join("; ");
}

export function buildOrgMatrixExportPayload(
  portfolios: readonly SellerPortfolio[],
  loadByPortfolioId: ReadonlyMap<string, PortfolioLoadItem> | undefined,
  directoryLabelFor: (userId: string, fallback?: string | null) => string,
): OrgMatrixExportPayload {
  const includeOpenValue = portfolios.some((portfolio) => {
    const load =
      loadByPortfolioId?.get(portfolio.id) ??
      resolvePortfolioLoad(null, portfolio.id, {
        customer_count: portfolio.customer_count,
        member_count:
          portfolio.member_count ??
          (portfolio.members?.length ? portfolio.members.length : 1),
      });
    return load.open_value != null;
  });

  const columns: Array<{ key: string; label: string }> = [
    { key: "portfolio", label: PORTFOLIO_LOAD_CONTENT.exportColPortfolio },
    { key: "members", label: PORTFOLIO_LOAD_CONTENT.exportColMembers },
    { key: "member_count", label: PORTFOLIO_LOAD_CONTENT.exportColMemberCount },
    { key: "customer_count", label: PORTFOLIO_LOAD_CONTENT.exportColCustomerCount },
  ];
  if (includeOpenValue) {
    columns.push({ key: "open_value", label: PORTFOLIO_LOAD_CONTENT.exportColOpenValue });
  }
  columns.push({ key: "status", label: PORTFOLIO_LOAD_CONTENT.exportColStatus });

  const rows = portfolios.map((portfolio) => {
    const load =
      loadByPortfolioId?.get(portfolio.id) ??
      resolvePortfolioLoad(null, portfolio.id, {
        customer_count: portfolio.customer_count,
        member_count:
          portfolio.member_count ??
          (portfolio.members?.length ? portfolio.members.length : 1),
      });
    const record: Record<string, unknown> = {
      portfolio: portfolio.display_name,
      members: memberLabels(portfolio, directoryLabelFor),
      member_count: load.member_count,
      customer_count: load.customer_count,
      status: portfolio.active
        ? PORTFOLIO_LOAD_CONTENT.exportStatusActive
        : PORTFOLIO_LOAD_CONTENT.exportStatusInactive,
    };
    if (includeOpenValue) {
      record.open_value =
        load.open_value == null
          ? PORTFOLIO_LOAD_CONTENT.openValueUnavailable
          : load.open_value;
    }
    return record;
  });

  return {
    title: PORTFOLIO_LOAD_CONTENT.exportMatrixTitle,
    columns,
    rows,
  };
}
