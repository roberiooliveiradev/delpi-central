import { describe, expect, it } from "vitest";

import {
  resolveWorklistNotification,
  resolveWorklistNotificationAudience,
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

  it("usa texto genérico para a equipe", () => {
    const note = resolveWorklistNotification(baseEvent({ reason: "task.created" }), "manager-1");
    expect(note.message).toBe("Ana Gestora atribuiu: Ligar ACME");
  });

  it("inclui ator em alterações", () => {
    const note = resolveWorklistNotification(
      baseEvent({ reason: "task.updated", assigneeUserIds: ["seller-b"] }),
      "seller-b",
    );
    expect(note.message).toBe("Ana Gestora alterou a tarefa: Ligar ACME");
  });
});
