import type { SellerPortfolio, SellerPortfolioMemberRole } from "../types/portfolio";

export type AdministrationMemberPortfolioRef = {
  portfolioId: string;
  displayName: string;
  role: SellerPortfolioMemberRole;
  active: boolean;
};

export type AdministrationMemberRow = {
  userId: string;
  /** Papel predominante: owner se for responsável em alguma carteira. */
  primaryRole: SellerPortfolioMemberRole;
  portfolios: AdministrationMemberPortfolioRef[];
};

/**
 * Monta roster pessoa × carteiras a partir de `members[]` (e fallback owner legado).
 */
export function buildAdministrationMembersRoster(
  portfolios: readonly SellerPortfolio[],
): AdministrationMemberRow[] {
  const byUser = new Map<string, AdministrationMemberRow>();

  const ensure = (userId: string): AdministrationMemberRow | null => {
    const id = userId.trim();
    if (!id) return null;
    let row = byUser.get(id);
    if (!row) {
      row = { userId: id, primaryRole: "member", portfolios: [] };
      byUser.set(id, row);
    }
    return row;
  };

  const addMembership = (
    userId: string,
    portfolio: SellerPortfolio,
    role: SellerPortfolioMemberRole,
  ) => {
    const row = ensure(userId);
    if (!row) return;
    if (row.portfolios.some((item) => item.portfolioId === portfolio.id)) return;
    row.portfolios.push({
      portfolioId: portfolio.id,
      displayName: portfolio.display_name,
      role,
      active: portfolio.active,
    });
    if (role === "owner") row.primaryRole = "owner";
  };

  for (const portfolio of portfolios) {
    const members = portfolio.members ?? [];
    if (members.length > 0) {
      for (const member of members) {
        addMembership(member.user_id, portfolio, member.role);
      }
      continue;
    }
    const ownerId = (portfolio.owner_user_id ?? portfolio.user_id ?? "").trim();
    if (ownerId) addMembership(ownerId, portfolio, "owner");
  }

  const rows = [...byUser.values()];
  for (const row of rows) {
    row.portfolios.sort((a, b) => a.displayName.localeCompare(b.displayName, "pt-BR"));
  }
  rows.sort((a, b) => {
    if (a.primaryRole !== b.primaryRole) {
      return a.primaryRole === "owner" ? -1 : 1;
    }
    return a.userId.localeCompare(b.userId);
  });
  return rows;
}
