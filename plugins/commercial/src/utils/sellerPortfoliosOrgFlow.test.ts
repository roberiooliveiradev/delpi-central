import { describe, expect, it } from "vitest";

import { buildSellerPortfoliosOrgFlowModel } from "./sellerPortfoliosOrgFlow";
import type { SellerPortfolio } from "../types/portfolio";

function portfolio(partial: Partial<SellerPortfolio> & Pick<SellerPortfolio, "id" | "display_name">): SellerPortfolio {
  return {
    user_id: partial.user_id ?? "owner-1",
    owner_user_id: partial.owner_user_id ?? partial.user_id ?? "owner-1",
    active: partial.active ?? true,
    customer_count: partial.customer_count ?? 2,
    customers: partial.customers ?? [],
    members: partial.members,
    member_count: partial.member_count,
    ...partial,
  };
}

describe("buildSellerPortfoliosOrgFlowModel", () => {
  const portfolios = [
    portfolio({
      id: "p1",
      display_name: "Sul",
      members: [
        { user_id: "u-ana", role: "owner" },
        { user_id: "u-pedro", role: "member" },
      ],
    }),
    portfolio({
      id: "p2",
      display_name: "Norte",
      user_id: "u-bruno",
      owner_user_id: "u-bruno",
      members: [{ user_id: "u-bruno", role: "owner" }],
    }),
  ];

  it("axis portfolio: roots are portfolios with person children", () => {
    const model = buildSellerPortfoliosOrgFlowModel({
      portfolios,
      axis: "portfolio",
      directoryLabelFor: (id) => id.toUpperCase(),
    });
    expect(model.nodes.filter((n) => n.kind === "portfolio")).toHaveLength(2);
    expect(model.edges.every((e) => e.source.startsWith("portfolio:"))).toBe(true);
    expect(model.edges).toHaveLength(3);
    const sul = model.nodes.find((n) => n.id === "portfolio:p1");
    expect(sul?.subtitle).toMatch(/cli/);
  });

  it("axis person: roots are people with portfolio children", () => {
    const model = buildSellerPortfoliosOrgFlowModel({
      portfolios,
      axis: "person",
      directoryLabelFor: (id) => `Label ${id}`,
    });
    const personRoots = model.nodes.filter((n) => n.kind === "person");
    expect(personRoots.length).toBeGreaterThanOrEqual(2);
    expect(model.edges.every((e) => e.source.startsWith("person:"))).toBe(true);
    expect(model.nodes.find((n) => n.id === "person:u-ana")?.title).toBe("Label u-ana");
  });
});
