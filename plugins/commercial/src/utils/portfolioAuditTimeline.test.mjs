#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  filterPortfolioAuditEvents,
  formatPortfolioAuditWhen,
  humanizePortfolioAuditMessage,
  mapPortfolioAuditEventsToTimelineItems,
  portfolioAuditEventFilterCategory,
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

  it("classifica e filtra eventos por categoria", () => {
    assert.equal(
      portfolioAuditEventFilterCategory("seller_portfolio.add_customer"),
      "customers",
    );
    assert.equal(
      portfolioAuditEventFilterCategory("seller_portfolio.set_owner"),
      "members",
    );
    assert.equal(
      portfolioAuditEventFilterCategory("seller_portfolio.deactivate"),
      "status",
    );
    assert.equal(
      portfolioAuditEventFilterCategory("seller_portfolio.transfer_customers"),
      "transfers",
    );

    const events = [
      {
        id: "1",
        action: "seller_portfolio.add_customer",
        actor_user_id: "a",
        entity_type: "seller_portfolio",
        entity_id: "p1",
        payload: {},
        created_at: null,
        title: "Cliente",
        message: "ok",
        tone: "success",
      },
      {
        id: "2",
        action: "seller_portfolio.add_member",
        actor_user_id: "a",
        entity_type: "seller_portfolio",
        entity_id: "p1",
        payload: {},
        created_at: null,
        title: "Membro",
        message: "ok",
        tone: "success",
      },
    ];
    assert.equal(filterPortfolioAuditEvents(events, "customers").length, 1);
    assert.equal(filterPortfolioAuditEvents(events, "all").length, 2);
  });

  it("substitui UUID e rótulo genérico pelo nome do diretório", () => {
    const uid = "3bfdd634-a3a5-41af-b6b3-607025c2bdf5";
    const message = humanizePortfolioAuditMessage(
      {
        id: "1",
        action: "seller_portfolio.remove_member",
        actor_user_id: "a",
        entity_type: "seller_portfolio",
        entity_id: "p1",
        payload: { user_id: uid },
        created_at: null,
        title: "Membro removido",
        message: `Usuário ${uid} removido da carteira.`,
        tone: "warning",
      },
      (id) => (id === uid ? "Maria Souza" : "Usuário"),
    );
    assert.equal(message, "Usuário Maria Souza removido da carteira.");
    assert.ok(!message.includes(uid));

    const generic = humanizePortfolioAuditMessage(
      {
        id: "2",
        action: "seller_portfolio.set_owner",
        actor_user_id: "a",
        entity_type: "seller_portfolio",
        entity_id: "p1",
        payload: { user_id: uid },
        created_at: null,
        title: "Responsável alterado",
        message: "Responsável definido: um usuário.",
        tone: "info",
      },
      (id) => (id === uid ? "Ana Gestora" : "Usuário"),
    );
    assert.equal(generic, "Responsável definido: Ana Gestora.");
  });
});
