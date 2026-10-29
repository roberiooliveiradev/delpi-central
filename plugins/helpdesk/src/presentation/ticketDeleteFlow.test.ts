import { describe, expect, it } from "vitest";

import { HelpdeskApiError } from "../api/helpdeskApi";
import {
  TICKET_DELETE_UNCONFIRMED_TEXT,
  canShowTicketDelete,
  consumeTicketDeleteNotice,
  stageTicketDeleteNotice,
  ticketDeleteConfirmed,
  ticketDeleteErrorText,
  ticketDeleteSuccessText,
} from "./ticketDeleteFlow";

describe("ticketDeleteFlow", () => {
  it("shows the affordance only on explicit can_delete — absent flag fails closed", () => {
    expect(canShowTicketDelete({ can_delete: true })).toBe(true);
    expect(canShowTicketDelete({ can_delete: false })).toBe(false);
    expect(canShowTicketDelete({})).toBe(false);
    expect(canShowTicketDelete(null)).toBe(false);
  });

  it("confirms only trash semantics — any other 2xx is unconfirmed", () => {
    expect(ticketDeleteConfirmed({ id: 7, deleted: true, delete_semantics: "trash" })).toBe(true);
    expect(ticketDeleteConfirmed({ id: 7, deleted: true })).toBe(false);
    expect(ticketDeleteConfirmed({ id: 7, delete_semantics: "trash" })).toBe(false);
    expect(ticketDeleteConfirmed({ id: 7, deleted: false, delete_semantics: "trash" })).toBe(false);
    expect(ticketDeleteConfirmed(null)).toBe(false);
  });

  it("maps delete errors to typed pt-BR copy without claiming success", () => {
    expect(ticketDeleteErrorText(new HelpdeskApiError("idempotency_in_flight", 409))).toContain(
      "tentativa anterior",
    );
    expect(ticketDeleteErrorText(new HelpdeskApiError("glpi_forbidden", 403))).toContain(
      "não permite excluir",
    );
    expect(ticketDeleteErrorText(new HelpdeskApiError("not_found", 404))).toContain(
      "não está mais disponível",
    );
    expect(ticketDeleteErrorText(new HelpdeskApiError("glpi_link_required", 409))).toContain(
      "sessão",
    );
    expect(ticketDeleteErrorText(new HelpdeskApiError("glpi_unavailable", 502))).toContain(
      "indisponível",
    );
    expect(ticketDeleteErrorText(new Error("boom"))).toBe(
      "Não foi possível excluir o chamado. Tente novamente.",
    );
    expect(TICKET_DELETE_UNCONFIRMED_TEXT).toContain("não confirmou");
  });

  it("stages the success notice exactly once across navigation", () => {
    const store = new Map<string, string>();
    (globalThis as { sessionStorage?: unknown }).sessionStorage = {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
    };
    try {
      expect(consumeTicketDeleteNotice()).toBeNull();
      stageTicketDeleteNotice(ticketDeleteSuccessText(7));
      expect(consumeTicketDeleteNotice()).toBe("Chamado #7 movido para a lixeira.");
      expect(consumeTicketDeleteNotice()).toBeNull();
    } finally {
      delete (globalThis as { sessionStorage?: unknown }).sessionStorage;
    }
  });
});
