#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  formatPortfolioCountValue,
  formatPortfolioRoleLabel,
  formatPortfoliosCount,
  listCommercialPermissions,
  listGrantedCapabilities,
} from "./userAccess.ts";

describe("userAccess helpers", () => {
  it("rotula só permissões commercial.*", () => {
    const items = listCommercialPermissions([
      "unrelated",
      "commercial.accounts.view",
      "commercial.worklist.view",
      "commercial.accounts.view",
    ]);
    assert.equal(items.length, 2);
    assert.equal(items[0]?.code, "commercial.accounts.view");
    assert.match(items[0]?.label || "", /Portal Comercial/i);
  });

  it("lista capacidades concedidas", () => {
    const items = listGrantedCapabilities({
      worklist_view: true,
      analytics_view: false,
      seller_portfolios_manage: true,
    });
    assert.equal(items.length, 2);
    assert.ok(items.every((item) => item.granted));
  });

  it("formata contagem de carteiras", () => {
    assert.match(formatPortfoliosCount(3), /3/);
  });

  it("não inventa Membro nem zero quando o contrato omite campos", () => {
    assert.equal(formatPortfolioRoleLabel(undefined), "—");
    assert.equal(formatPortfolioRoleLabel("owner"), "Responsável");
    assert.equal(formatPortfolioRoleLabel("member"), "Membro");
    assert.equal(formatPortfolioCountValue(undefined), "—");
    assert.equal(formatPortfolioCountValue(null), "—");
    assert.equal(formatPortfolioCountValue(0), "0");
    assert.equal(formatPortfolioCountValue(2), "2");
  });
});
