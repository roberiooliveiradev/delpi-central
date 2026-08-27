import { describe, expect, it } from "vitest";

import { resolveSignInviteMailBadge } from "./signInviteMailBadge";

describe("resolveSignInviteMailBadge", () => {
  it("maps accepted + delivered to success", () => {
    const badge = resolveSignInviteMailBadge({
      send_status: "accepted",
      delivery_status: "delivered",
      delivery_status_label: "Entregue",
    });
    expect(badge?.variant).toBe("success");
  });
});
