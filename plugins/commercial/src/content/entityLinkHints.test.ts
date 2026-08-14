import { describe, expect, it } from "vitest";

import {
  accountLinkTitle,
  opPageLinkTitle,
  orderLinkTitle,
  otdLineLinkTitle,
  profileLinkTitle,
} from "./entityLinkHints";

describe("entityLinkHints", () => {
  it("formata hints Abrir…", () => {
    expect(accountLinkTitle("WEG")).toBe("Abrir conta de WEG");
    expect(profileLinkTitle("Ana")).toBe("Abrir perfil de Ana");
    expect(opPageLinkTitle("00118901001")).toBe("Abrir página da OP 00118901001");
    expect(orderLinkTitle("102942", "01")).toBe("Abrir pedido 102942/01");
    expect(otdLineLinkTitle("102942", "01")).toBe("Abrir linha OTD 102942/01");
  });
});
