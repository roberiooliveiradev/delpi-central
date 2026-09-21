import { describe, expect, it } from "vitest";

import { parseHelpdeskRoute } from "./helpdeskRoute";

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
});
