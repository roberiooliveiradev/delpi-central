import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isCustomerInViewerPortfolios,
  shouldShowEphemeralClientNav,
} from "./customerMembership.ts";

describe("customerMembership", () => {
  const portfolios = [
    {
      id: "p1",
      user_id: "u1",
      display_name: "Carteira",
      active: true,
      customer_count: 1,
      customers: [
        {
          customer_code: "000123",
          customer_store: "01",
          customer_name: "Acme",
        },
      ],
    },
  ];

  it("detecta membership por código/loja", () => {
    assert.equal(
      isCustomerInViewerPortfolios("000123", "01", portfolios),
      true,
    );
    assert.equal(
      isCustomerInViewerPortfolios("999", "01", portfolios),
      false,
    );
  });

  it("Cliente efêmero só fora da carteira sem team/manage", () => {
    assert.equal(
      shouldShowEphemeralClientNav({
        inMembership: false,
        canUseTeamScope: false,
        canManagePortfolios: false,
      }),
      true,
    );
    assert.equal(
      shouldShowEphemeralClientNav({
        inMembership: true,
        canUseTeamScope: false,
        canManagePortfolios: false,
      }),
      false,
    );
    assert.equal(
      shouldShowEphemeralClientNav({
        inMembership: false,
        canUseTeamScope: true,
        canManagePortfolios: false,
      }),
      false,
    );
    assert.equal(
      shouldShowEphemeralClientNav({
        inMembership: false,
        canUseTeamScope: false,
        canManagePortfolios: true,
      }),
      false,
    );
  });
});
