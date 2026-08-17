import { describe, expect, it } from "vitest";

import { accountLinkTitle } from "../../../content/entityLinkHints";
import { buildCustomerDetailHref } from "../../../app/pluginNavigation";

describe("OtdCustomerIdentity / CustomerAvatar href contract", () => {
  it("Conta href + title Abrir conta", () => {
    const href = buildCustomerDetailHref("0001", "01", { search: "" });
    expect(href).toContain("/customers/0001/01");
    expect(accountLinkTitle("WEG")).toBe("Abrir conta de WEG");
  });
});
