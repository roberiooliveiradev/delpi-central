import { describe, expect, it } from "vitest";

import { parseHelpdeskRoute, ticketDetailPath, isModifiedHelpdeskClick } from "./helpdeskRoute";

describe("parseHelpdeskRoute", () => {
  it("abre a lista no path do módulo", () => {
    expect(parseHelpdeskRoute("/apps/helpdesk")).toEqual({ kind: "list" });
    expect(parseHelpdeskRoute("/apps/helpdesk/")).toEqual({ kind: "list" });
  });

  it("mantém o detalhe após F5 no id do chamado", () => {
    expect(parseHelpdeskRoute("/apps/helpdesk/tickets/42")).toEqual({
      kind: "detail",
      ticketId: "42",
    });
  });

  it("não trata texto livre como id de chamado", () => {
    expect(parseHelpdeskRoute("/apps/helpdesk/tickets/abc")).toEqual({ kind: "unknown" });
  });

  it("monta o path estável do detalhe", () => {
    expect(ticketDetailPath(1120)).toBe("/apps/helpdesk/tickets/1120");
    expect(ticketDetailPath("42")).toBe("/apps/helpdesk/tickets/42");
  });

  it("reconhece clique com modificador para abrir em outra aba", () => {
    expect(isModifiedHelpdeskClick({ metaKey: true, ctrlKey: false, shiftKey: false, altKey: false })).toBe(true);
    expect(isModifiedHelpdeskClick({ metaKey: false, ctrlKey: true, shiftKey: false, altKey: false })).toBe(true);
    expect(isModifiedHelpdeskClick({ metaKey: false, ctrlKey: false, shiftKey: true, altKey: false })).toBe(true);
    expect(isModifiedHelpdeskClick({ metaKey: false, ctrlKey: false, shiftKey: false, altKey: true })).toBe(true);
    expect(isModifiedHelpdeskClick({ metaKey: false, ctrlKey: false, shiftKey: false, altKey: false, button: 1 })).toBe(
      true,
    );
    expect(isModifiedHelpdeskClick({ metaKey: false, ctrlKey: false, shiftKey: false, altKey: false, button: 0 })).toBe(
      false,
    );
  });
});
