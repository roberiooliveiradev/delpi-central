import { describe, expect, it } from "vitest";

import { resolveSignInviteMailBadge } from "./signInviteMailBadge";

describe("resolveSignInviteMailBadge", () => {
  it("returns null for pending or missing mail", () => {
    expect(resolveSignInviteMailBadge(null)).toBeNull();
    expect(resolveSignInviteMailBadge({ send_status: "pending" })).toBeNull();
  });

  it("maps accepted + trace_pending to warning", () => {
    const badge = resolveSignInviteMailBadge({
      send_status: "accepted",
      delivery_status: "trace_pending",
      send_status_label: "Enviado",
      delivery_status_label: "Aguardando confirmação",
      badge_hint: "Enviado — aguardando confirmação de entrega",
    });
    expect(badge?.variant).toBe("warning");
    expect(badge?.label).toBe("Aguardando confirmação");
  });

  it("maps delivered to success", () => {
    const badge = resolveSignInviteMailBadge({
      send_status: "accepted",
      delivery_status: "delivered",
      send_status_label: "Enviado",
      delivery_status_label: "Entregue",
    });
    expect(badge?.variant).toBe("success");
    expect(badge?.label).toBe("Entregue");
  });

  it("maps skipped_no_email to danger", () => {
    const badge = resolveSignInviteMailBadge({
      send_status: "skipped_no_email",
      send_status_label: "Sem e-mail",
    });
    expect(badge?.variant).toBe("danger");
  });
});
