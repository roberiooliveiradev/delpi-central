import { describe, expect, it } from "vitest";

import {
  resolvePortfolioNotification,
  resolveWorklistNotification,
  resolveWorklistNotificationAudience,
  portfolioEventTouchesId,
  type CommercialPortfolioChangedEvent,
  type CommercialWorklistChangedEvent,
} from "./realtime";

function baseEvent(
  overrides: Partial<CommercialWorklistChangedEvent> = {},
): CommercialWorklistChangedEvent {
  return {
    type: "worklist.changed",
    reason: "task.reassigned",
    taskId: "t1",
    taskTitle: "Ligar ACME",
    assigneeUserIds: ["seller-b", "seller-a"],
    actorDisplayName: "Ana Gestora",
    assigneeDisplayName: "Bruno Vendedor",
    ...overrides,
  };
}

describe("resolveWorklistNotificationAudience", () => {
  it("marca responsável atual como assignee", () => {
    expect(resolveWorklistNotificationAudience(baseEvent(), "seller-b")).toBe("assignee");
  });

  it("marca responsável anterior como previous", () => {
    expect(resolveWorklistNotificationAudience(baseEvent(), "seller-a")).toBe("previous");
  });

  it("marca gestor como team", () => {
    expect(resolveWorklistNotificationAudience(baseEvent(), "manager-1")).toBe("team");
  });
});

describe("resolveWorklistNotification", () => {
  it("indica quem atribuiu ao responsável", () => {
    const note = resolveWorklistNotification(baseEvent(), "seller-b");
    expect(note.message).toBe("Ana Gestora atribuiu a você: Ligar ACME");
  });

  it("inclui ator e responsável na atribuição para a equipe", () => {
    const note = resolveWorklistNotification(baseEvent({ reason: "task.created" }), "manager-1");
    expect(note.message).toBe("Ana Gestora atribuiu a Bruno Vendedor: Ligar ACME");
  });

  it("inclui ator em alterações", () => {
    const note = resolveWorklistNotification(
      baseEvent({ reason: "task.updated", assigneeUserIds: ["seller-b"] }),
      "seller-b",
    );
    expect(note.message).toBe("Ana Gestora alterou a tarefa: Ligar ACME");
  });

  it("inclui ator em conclusões", () => {
    const note = resolveWorklistNotification(
      baseEvent({ reason: "task.completed", assigneeUserIds: ["seller-b"] }),
      "manager-1",
    );
    expect(note.message).toBe("Ana Gestora concluiu: Ligar ACME");
  });
});

describe("resolvePortfolioNotification", () => {
  it("prioriza notification do servidor", () => {
    const event: CommercialPortfolioChangedEvent = {
      type: "portfolio.changed",
      reason: "seller_portfolio.add_customer",
      portfolioId: "p1",
      displayName: "Sul",
      actorDisplayName: "Ana",
      notification: {
        title: "Cliente vinculado",
        message: "Ana vinculou um cliente em Sul.",
        variant: "info",
      },
    };
    expect(resolvePortfolioNotification(event)).toEqual(event.notification);
  });

  it("usa fallback local sem notification", () => {
    const note = resolvePortfolioNotification({
      type: "portfolio.changed",
      reason: "seller_portfolio.add_member",
      portfolioId: "p1",
      displayName: "Norte",
      actorDisplayName: "Bruno",
    });
    expect(note.title).toBe("Carteira atualizada");
    expect(note.message).toContain("Bruno");
    expect(note.message).toContain("Norte");
  });

  it("substitui Alguém da equipe quando o ator é resolvido", () => {
    const note = resolvePortfolioNotification({
      type: "portfolio.changed",
      reason: "seller_portfolio.add_customer",
      portfolioId: "p1",
      displayName: "Carteira Teste",
      actorDisplayName: "João Silva",
      notification: {
        title: "Cliente vinculado",
        message: "Alguém da equipe vinculou um cliente em «Carteira Teste».",
        variant: "success",
      },
    });
    expect(note.message).toBe("João Silva vinculou um cliente em «Carteira Teste».");
  });
});

describe("portfolioEventTouchesId", () => {
  it("bate portfolioId e portfolioIds", () => {
    const event: CommercialPortfolioChangedEvent = {
      type: "portfolio.changed",
      reason: "transfer",
      portfolioId: "a",
      portfolioIds: ["a", "b"],
    };
    expect(portfolioEventTouchesId(event, "a")).toBe(true);
    expect(portfolioEventTouchesId(event, "b")).toBe(true);
    expect(portfolioEventTouchesId(event, "c")).toBe(false);
  });
});
