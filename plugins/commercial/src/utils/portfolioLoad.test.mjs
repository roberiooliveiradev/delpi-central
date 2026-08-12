#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  formatAttentionCount,
  formatCompactOpenValue,
  formatPersonLoadSnippet,
  formatPortfolioLoadSnippet,
  personLoadByUserId,
  portfolioLoadById,
  resolvePortfolioLoad,
} from "./portfolioLoad.ts";

const SUMMARY = {
  portfolios: [
    {
      id: "p1",
      display_name: "Sul",
      active: true,
      customer_count: 5,
      member_count: 2,
      open_value: null,
      attention_count: null,
    },
  ],
  by_person: [
    {
      user_id: "ana",
      portfolio_ids: ["p1", "p2"],
      portfolio_count: 2,
      customer_count: 8,
      open_value: 1_700_000,
      attention_count: 4,
    },
  ],
  totvs_metrics: {
    available: false,
    reason: "open_orders_aggregation_not_wired",
  },
};

describe("portfolioLoad helpers", () => {
  it("indexa load por carteira e pessoa", () => {
    assert.equal(portfolioLoadById(SUMMARY).get("p1")?.customer_count, 5);
    assert.equal(personLoadByUserId(SUMMARY).get("ana")?.portfolio_count, 2);
  });

  it("resolve fallback quando summary não tem a carteira", () => {
    const load = resolvePortfolioLoad(SUMMARY, "missing", {
      customer_count: 3,
      member_count: 1,
    });
    assert.equal(load.customer_count, 3);
    assert.equal(load.member_count, 1);
    assert.equal(load.open_value, null);
  });

  it("formata valor compacto e snippet com stub", () => {
    assert.equal(formatCompactOpenValue(null), "—");
    assert.equal(formatCompactOpenValue(1_700_000), "R$ 1,7 mi");
    assert.equal(formatCompactOpenValue(850_000), "R$ 850 mil");
    assert.equal(formatAttentionCount(null), "Atenção —");
    assert.equal(formatAttentionCount(4), "Atenção 4");
    assert.equal(
      formatPortfolioLoadSnippet(SUMMARY.portfolios[0]),
      "5 cli · — · Atenção — · 2 membros",
    );
    assert.equal(
      formatPersonLoadSnippet(SUMMARY.by_person[0]),
      "8 cli · R$ 1,7 mi · Atenção 4 · 2 carteiras",
    );
  });
});
