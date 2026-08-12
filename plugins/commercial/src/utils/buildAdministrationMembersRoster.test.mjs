#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildAdministrationMembersRoster } from "./buildAdministrationMembersRoster.ts";

describe("buildAdministrationMembersRoster", () => {
  it("agrega pessoa em várias carteiras e prioriza papel owner", () => {
    const rows = buildAdministrationMembersRoster([
      {
        id: "p1",
        user_id: "u-owner",
        owner_user_id: "u-owner",
        display_name: "Carteira A",
        active: true,
        customer_count: 2,
        customers: [],
        members: [
          { user_id: "u-owner", role: "owner" },
          { user_id: "u-shared", role: "member" },
        ],
      },
      {
        id: "p2",
        user_id: "u-shared",
        owner_user_id: "u-shared",
        display_name: "Carteira B",
        active: true,
        customer_count: 1,
        customers: [],
        members: [
          { user_id: "u-shared", role: "owner" },
          { user_id: "u-owner", role: "member" },
        ],
      },
    ]);

    assert.equal(rows.length, 2);
    const owner = rows.find((row) => row.userId === "u-owner");
    const shared = rows.find((row) => row.userId === "u-shared");
    assert.ok(owner);
    assert.ok(shared);
    assert.equal(owner.primaryRole, "owner");
    assert.equal(shared.primaryRole, "owner");
    assert.equal(owner.portfolios.length, 2);
    assert.equal(shared.portfolios.length, 2);
  });

  it("usa owner legado quando members está vazio", () => {
    const rows = buildAdministrationMembersRoster([
      {
        id: "p1",
        user_id: "legacy-owner",
        display_name: "Só legado",
        active: false,
        customer_count: 0,
        customers: [],
      },
    ]);
    assert.deepEqual(rows, [
      {
        userId: "legacy-owner",
        primaryRole: "owner",
        portfolios: [
          {
            portfolioId: "p1",
            displayName: "Só legado",
            role: "owner",
            active: false,
          },
        ],
      },
    ]);
  });
});
