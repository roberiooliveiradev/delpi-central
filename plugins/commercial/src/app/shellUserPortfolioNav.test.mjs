#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildShellPortfolioCustomersSearch,
  resolveShellUserPortfolioNavMode,
  shellPortfolioSellerAccess,
} from "./shellUserPortfolioNav.ts";

describe("resolveShellUserPortfolioNavMode", () => {
  it("desabilita quando não há carteiras", () => {
    assert.deepEqual(resolveShellUserPortfolioNavMode([]), { kind: "disabled" });
    assert.deepEqual(resolveShellUserPortfolioNavMode([{ id: "  ", display_name: "X" }]), {
      kind: "disabled",
    });
  });

  it("vai direto com uma carteira", () => {
    assert.deepEqual(
      resolveShellUserPortfolioNavMode([{ id: "p1", display_name: "Carteira A" }]),
      {
        kind: "direct",
        portfolio: { id: "p1", displayName: "Carteira A" },
      },
    );
  });

  it("abre menu com mais de uma carteira", () => {
    const mode = resolveShellUserPortfolioNavMode([
      { id: "p1", display_name: "A" },
      { id: "p2", display_name: "B" },
    ]);
    assert.equal(mode.kind, "menu");
    if (mode.kind !== "menu") return;
    assert.equal(mode.portfolios.length, 2);
    assert.equal(mode.portfolios[0]?.displayName, "A");
  });
});

describe("buildShellPortfolioCustomersSearch", () => {
  it("não injeta seller_id com carteira única", () => {
    assert.equal(buildShellPortfolioCustomersSearch("p1", ["p1"]), "");
    assert.deepEqual(shellPortfolioSellerAccess(["p1"]), {
      allowSellerId: false,
      validSellerIds: [],
    });
  });

  it("injeta seller_id quando há mais de uma carteira", () => {
    assert.equal(
      buildShellPortfolioCustomersSearch("p2", ["p1", "p2"]),
      "?seller_id=p2",
    );
  });
});
