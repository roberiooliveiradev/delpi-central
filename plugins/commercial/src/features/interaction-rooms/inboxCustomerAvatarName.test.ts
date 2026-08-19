import { describe, expect, it } from "vitest";

import { inboxCustomerAvatarName } from "./inboxCustomerAvatarName";

describe("inboxCustomerAvatarName", () => {
  it("usa o nome do cliente e ignora título de pedido", () => {
    expect(
      inboxCustomerAvatarName({ customer_name: "TRAMAR" }),
    ).toBe("TRAMAR");
    expect(
      inboxCustomerAvatarName({ customer_name: "  BUHLER  " }),
    ).toBe("BUHLER");
    expect(inboxCustomerAvatarName({ customer_name: null })).toBe("");
    expect(inboxCustomerAvatarName({ customer_name: "   " })).toBe("");
  });
});
