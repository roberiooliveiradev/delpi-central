import { describe, expect, it } from "vitest";

import {
  defaultTicketWorkspaceAction,
  ticketWorkspaceActionById,
  ticketWorkspaceActions,
} from "./ticketWorkspaceActions";

describe("ticketWorkspaceActions", () => {
  it("reply + attach when followup allowed", () => {
    const actions = ticketWorkspaceActions({ can_followup: true });
    expect(actions.map((item) => item.id)).toEqual(["reply", "attach_file"]);
  });

  it("hides reply when can_followup is false", () => {
    const actions = ticketWorkspaceActions({ can_followup: false });
    expect(actions.map((item) => item.id)).toEqual([]);
  });

  it("adds technician ops only from semantic capabilities", () => {
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

  it("does not invent ops without capabilities", () => {
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

  it("defaults to reply when available", () => {
    expect(
      defaultTicketWorkspaceAction(
        ticketWorkspaceActions({
          can_followup: false,
          can_accept_solution: true,
        }),
      ),
    ).toBe("accept_solution");
    expect(defaultTicketWorkspaceAction(ticketWorkspaceActions({ can_followup: true }))).toBe(
      "reply",
    );
  });

  it("resolves action by id", () => {
    const actions = ticketWorkspaceActions({ can_followup: true, can_create_solution: true });
    expect(ticketWorkspaceActionById(actions, "create_solution")?.label).toBe("Adicionar solução");
    expect(ticketWorkspaceActionById(actions, "accept_solution")).toBeNull();
  });

  it("labels attachment as file attach not document entity", () => {
    const attach = ticketWorkspaceActions({ can_followup: true }).find(
      (item) => item.id === "attach_file",
    );
    expect(attach?.label).toBe("Anexar arquivo");
  });
});
