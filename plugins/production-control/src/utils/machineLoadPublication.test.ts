import { describe, expect, it } from "vitest";

import { describeMachineLoadPublication } from "./machineLoadPublication";

describe("describeMachineLoadPublication", () => {
  it("live: Enviado às máquinas, sem botão de envio", () => {
    const view = describeMachineLoadPublication({
      state: "live",
      published_at: "2026-10-07T14:32:00Z",
      published_by: "Maria",
    });

    expect(view.label).toBe("Enviado às máquinas");
    expect(view.canPublish).toBe(false);
    expect(view.hint).toContain("Último envio:");
    expect(view.hint).toContain("Maria");
  });

  it("live sem usuário conhecido: mostra só o horário", () => {
    const view = describeMachineLoadPublication({
      state: "live",
      published_at: "2026-10-07T14:32:00Z",
      published_by: null,
    });

    expect(view.hint).toContain("Último envio:");
    expect(view.hint).not.toContain(" por ");
  });

  it("draft: Em preparação + explicação + botão", () => {
    const view = describeMachineLoadPublication({
      state: "draft",
      published_at: "2026-10-07T10:00:00Z",
      published_by: "pcp",
    });

    expect(view.label).toBe("Em preparação");
    expect(view.canPublish).toBe(true);
    expect(view.hint).toContain("última programação enviada");
    expect(view.hint).toContain("Último envio às máquinas:");
  });

  it("unpublished: Em preparação + texto de primeira publicação + botão", () => {
    const view = describeMachineLoadPublication({
      state: "unpublished",
      published_at: null,
      published_by: null,
    });

    expect(view.label).toBe("Em preparação");
    expect(view.canPublish).toBe(true);
    expect(view.hint).toBe("Esta carga ainda não foi enviada para as máquinas.");
  });

  it("payload antigo sem publication: comporta-se como unpublished", () => {
    const view = describeMachineLoadPublication(undefined);

    expect(view.label).toBe("Em preparação");
    expect(view.canPublish).toBe(true);
  });
});
