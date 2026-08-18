import { describe, expect, it } from "vitest";

import {
  buildCustomerEntityKey,
  buildOrderEntityKey,
  buildProductionOrderEntityKey,
} from "./interactionRoomEntityKeys";

describe("interactionRoomEntityKeys", () => {
  it("monta chaves estáveis com pipe", () => {
    expect(buildCustomerEntityKey("0001", "01")).toBe("0001|01");
    expect(buildOrderEntityKey("01", "102942")).toBe("01|102942");
    expect(buildProductionOrderEntityKey("01", "OP99")).toBe("01|OP99");
    expect(buildCustomerEntityKey("", "01")).toBeNull();
    expect(buildOrderEntityKey("01", "")).toBeNull();
  });
});
