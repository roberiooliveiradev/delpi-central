import { describe, expect, it } from "vitest";

import { HELPDESK_FORCE_CARDS_MAX_WIDTH, shouldForceTicketCards } from "./listViewport";

describe("shouldForceTicketCards", () => {
  it("força cards em mobile/tablet estreito", () => {
    expect(shouldForceTicketCards(360)).toBe(true);
    expect(shouldForceTicketCards(HELPDESK_FORCE_CARDS_MAX_WIDTH)).toBe(true);
  });

  it("mantém preferência de layout em desktop", () => {
    expect(shouldForceTicketCards(HELPDESK_FORCE_CARDS_MAX_WIDTH + 1)).toBe(false);
    expect(shouldForceTicketCards(1440)).toBe(false);
  });

  it("não força com viewport inválido", () => {
    expect(shouldForceTicketCards(0)).toBe(false);
    expect(shouldForceTicketCards(Number.NaN)).toBe(false);
  });
});
