#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { PORTFOLIO_LOAD_CONTENT } from "../content/portfolioLoadContent.ts";
import { buildOrgMatrixExportPayload } from "./orgMatrixExportPayload.ts";

describe("orgMatrixExportPayload", () => {
  it("monta colunas PT-BR com membros, clientes e valor aberto quando presente", () => {
    const portfolios = [
      {
        id: "p1",
        user_id: "u1",
        owner_user_id: "u1",
        display_name: "Sul",
        active: true,
        customer_count: 5,
        member_count: 2,
        customers: [],
        members: [
          { user_id: "u1", role: "owner" },
          { user_id: "u2", role: "member" },
        ],
      },
    ];
    const loadByPortfolioId = new Map([
      [
        "p1",
        {
          id: "p1",
          display_name: "Sul",
          active: true,
          customer_count: 5,
          member_count: 2,
          open_value: 1500,
          attention_count: null,
        },
      ],
    ]);
    const payload = buildOrgMatrixExportPayload(portfolios, loadByPortfolioId, (id) =>
      id === "u1" ? "Ana" : "Bruno",
    );
    assert.equal(payload.title, PORTFOLIO_LOAD_CONTENT.exportMatrixTitle);
    assert.deepEqual(
      payload.columns.map((column) => column.label),
      [
        PORTFOLIO_LOAD_CONTENT.exportColPortfolio,
        PORTFOLIO_LOAD_CONTENT.exportColMembers,
        PORTFOLIO_LOAD_CONTENT.exportColMemberCount,
        PORTFOLIO_LOAD_CONTENT.exportColCustomerCount,
        PORTFOLIO_LOAD_CONTENT.exportColOpenValue,
        PORTFOLIO_LOAD_CONTENT.exportColStatus,
      ],
    );
    assert.equal(payload.rows[0].portfolio, "Sul");
    assert.equal(payload.rows[0].members, "Ana; Bruno");
    assert.equal(payload.rows[0].customer_count, 5);
    assert.equal(payload.rows[0].open_value, 1500);
    assert.equal(payload.rows[0].status, PORTFOLIO_LOAD_CONTENT.exportStatusActive);
  });

  it("omite valor aberto quando todos são null", () => {
    const portfolios = [
      {
        id: "p2",
        user_id: "u9",
        display_name: "Norte",
        active: false,
        customer_count: 1,
        customers: [],
        members: [],
      },
    ];
    const payload = buildOrgMatrixExportPayload(portfolios, undefined, (id) => id);
    assert.equal(
      payload.columns.some((column) => column.key === "open_value"),
      false,
    );
    assert.equal(payload.rows[0].status, PORTFOLIO_LOAD_CONTENT.exportStatusInactive);
  });
});
