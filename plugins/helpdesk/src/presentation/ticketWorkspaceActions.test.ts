import { describe, expect, it } from "vitest";
import {
  defaultTicketWorkspaceAction,
  ticketWorkspaceActions,
  ticketWorkspaceActionById,
} from "./ticketWorkspaceActions";

describe("ticketWorkspaceActions", () => {
  it("reply + document when followup allowed", () => {
    const actions = ticketWorkspaceActions({ can_followup: true });
    expect(actions.map((item) => item.id)).toEqual(["reply", "add_document"]);
  });

  it("hides reply when can_followup is false", () => {
    const actions = ticketWorkspaceActions({ can_followup: false });
    expect(actions.map((item) => item.id)).not.toContain("reply");
    expect(actions.map((item) => item.id)).not.toContain("add_document");
  });

  it("includes accept/reject only when ticket capabilities say so", () => {
    const actions = ticketWorkspaceActions({
      can_followup: true,
      can_accept_solution: true,
      can_reject_solution: true,
    });
    expect(actions.map((item) => item.id)).toEqual([
      "reply",
      "add_document",
      "accept_solution",
      "reject_solution",
    ]);
  });

  it("does not invent solution-create, task or approval request", () => {
    const actions = ticketWorkspaceActions({
      can_followup: true,
      can_accept_solution: true,
      can_reject_solution: true,
    });
    expect(actions.map((item) => item.id).join(",")).not.toMatch(
      /create_solution|add_solution|task|approval_request|pedir/i,
    );
  });

  it("defaults to reply when available", () => {
    const actions = ticketWorkspaceActions({
      can_followup: false,
      can_accept_solution: true,
    });
    expect(defaultTicketWorkspaceAction(actions)).toBe("accept_solution");
    expect(defaultTicketWorkspaceAction(ticketWorkspaceActions({ can_followup: true }))).toBe(
      "reply",
    );
  });

  it("resolves action by id", () => {
    const actions = ticketWorkspaceActions({ can_followup: true });
    expect(ticketWorkspaceActionById(actions, "reply")?.label).toBe("Responder");
    expect(ticketWorkspaceActionById(actions, "add_document")?.label).toBe("Adicionar documento");
    expect(ticketWorkspaceActionById(actions, "accept_solution")).toBeNull();
  });
});
