import { describe, expect, it } from "vitest";

import {
  defaultTicketWorkspaceAction,
  ticketWorkspaceActions,
  ticketWorkspaceActionById,
  ticketWorkspaceSelectorActions,
} from "./ticketWorkspaceActions";
import { ticketActionPresentation } from "./ticketActionPresentation";
import {
  conversationMessageVisible,
  DEFAULT_TIMELINE_VISIBILITY,
} from "./timelineVisibility";

describe("ticketWorkspaceActions", () => {
  it("exposes reply when can_followup is true", () => {
    const actions = ticketWorkspaceActions({ can_followup: true });
    expect(actions.map((item) => item.id)).toContain("reply");
  });

  it("omits reply when can_followup is false", () => {
    const actions = ticketWorkspaceActions({ can_followup: false });
    expect(actions.map((item) => item.id)).not.toContain("reply");
  });

  it("includes proven technician ops when capabilities are true", () => {
    const actions = ticketWorkspaceActions({
      can_followup: true,
      can_create_solution: true,
      can_create_task: true,
      can_request_approval: true,
      can_accept_solution: true,
      can_reject_solution: true,
    });
    expect(actions.map((item) => item.id)).toEqual([
      "reply",
      "create_solution",
      "create_task",
      "attach_file",
      "request_approval",
      "accept_solution",
      "reject_solution",
    ]);
  });

  it("keeps selector without accept/reject lifecycle actions", () => {
    const actions = ticketWorkspaceActions({
      can_followup: true,
      can_create_solution: true,
      can_accept_solution: true,
      can_reject_solution: true,
    });
    expect(ticketWorkspaceSelectorActions(actions).map((item) => item.id)).toEqual([
      "reply",
      "create_solution",
      "attach_file",
    ]);
  });

  it("omits technician ops when capabilities are false", () => {
    const actions = ticketWorkspaceActions({
      can_followup: true,
      can_create_solution: false,
      can_create_task: false,
      can_request_approval: false,
    });
    expect(actions.map((item) => item.id).join(",")).not.toMatch(
      /create_solution|create_task|request_approval/,
    );
  });

  it("defaults to idle (no composer open)", () => {
    expect(defaultTicketWorkspaceAction(ticketWorkspaceActions({ can_followup: true }))).toBeNull();
    expect(
      defaultTicketWorkspaceAction(
        ticketWorkspaceActions({
          can_followup: false,
          can_accept_solution: true,
        }),
      ),
    ).toBeNull();
  });

  it("resolves action by id", () => {
    const actions = ticketWorkspaceActions({ can_followup: true, can_create_solution: true });
    expect(ticketWorkspaceActionById(actions, "create_solution")?.label).toBe("Adicionar solução");
    expect(ticketWorkspaceActionById(actions, "accept_solution")).toBeNull();
  });

  it("keeps attach_file when followup is allowed", () => {
    const attach = ticketWorkspaceActions({ can_followup: true }).find(
      (item) => item.id === "attach_file",
    );
    expect(attach?.label).toBe("Anexar arquivo");
  });
});

describe("ticketActionPresentation", () => {
  it("assigns distinct semantic variants and icons", () => {
    expect(ticketActionPresentation("reply").variant).toBe("reply");
    expect(ticketActionPresentation("create_task").variant).toBe("task");
    expect(ticketActionPresentation("create_solution").variant).toBe("solution");
    expect(ticketActionPresentation("attach_file").variant).toBe("attachment");
    expect(ticketActionPresentation("request_approval").variant).toBe("approval");
    expect(ticketActionPresentation("reply").submitLabel).toBe("Enviar resposta");
    expect(ticketActionPresentation("create_task").submitLabel).toBe("Criar tarefa");
  });
});

describe("timelineVisibility", () => {
  it("filters conversation kinds by visibility state", () => {
    const hiddenTasks = { ...DEFAULT_TIMELINE_VISIBILITY, tasks: false };
    expect(conversationMessageVisible("task", hiddenTasks)).toBe(false);
    expect(conversationMessageVisible("followup", hiddenTasks)).toBe(true);
    expect(conversationMessageVisible("opening", { ...DEFAULT_TIMELINE_VISIBILITY, description: false })).toBe(
      false,
    );
  });
});
