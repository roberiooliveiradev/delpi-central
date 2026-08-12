#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  formatPortfolioAuditWhen,
  mapPortfolioAuditEventsToTimelineItems,
  toPortfolioAuditTimelineTone,
} from "./portfolioAuditTimeline.ts";

describe("portfolioAuditTimeline", () => {
  it("mapeia tom da API para o Timeline do kit", () => {
    assert.equal(toPortfolioAuditTimelineTone("success"), "success");
    assert.equal(toPortfolioAuditTimelineTone("danger"), "danger");
    assert.equal(toPortfolioAuditTimelineTone("weird"), "default");
  });

  it("ordena eventos do mais recente ao mais antigo", () => {
    const items = mapPortfolioAuditEventsToTimelineItems([
      {
        id: "1",
        action: "seller_portfolio.add_member",
        actor_user_id: "a",
        entity_type: "seller_portfolio",
        entity_id: "p1",
        payload: {},
        created_at: "2026-01-01T10:00:00Z",
        title: "Antigo",
        message: "msg",
        tone: "info",
      },
      {
        id: "2",
        action: "seller_portfolio.deactivate",
        actor_user_id: "a",
        entity_type: "seller_portfolio",
        entity_id: "p1",
        payload: {},
        created_at: "2026-08-01T10:00:00Z",
        title: "Novo",
        message: "msg",
        tone: "warning",
      },
    ]);
    assert.equal(items[0]?.id, "2");
    assert.equal(items[1]?.id, "1");
    assert.ok(formatPortfolioAuditWhen("2026-08-01T10:00:00Z").length > 0);
  });
});
