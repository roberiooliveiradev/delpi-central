import { describe, expect, it } from "vitest";

import {
  formatRoomEntityPresentation,
  parseOrderEntityKey,
} from "./interactionRoomEntityPresentation";

describe("interactionRoomEntityPresentation", () => {
  it("parseia filial|pedido sem expor pipe na UI", () => {
    expect(parseOrderEntityKey("02|002573")).toEqual({
      unitCode: "02",
      orderNumber: "002573",
    });
    expect(parseOrderEntityKey("")).toBeNull();
    expect(parseOrderEntityKey("02|")).toBeNull();
  });

  it("formata Unidade com estado (Espírito Santo), zero Filial 02", () => {
    const result = formatRoomEntityPresentation(
      "order",
      "02|002573",
      "Pedido 002573",
    );
    expect(result.primaryNumber).toBe("002573");
    expect(result.chipLabel).toBe("Espírito Santo");
    expect(result.unitLabel).toBe("Espírito Santo");
    expect(result.aboutFields).toEqual([
      { label: "Pedido", value: "002573" },
      { label: "Unidade", value: "Espírito Santo" },
    ]);
    expect(JSON.stringify(result)).not.toMatch(/02\|002573/);
    expect(JSON.stringify(result)).not.toMatch(/Filial 02/);
  });

  it("formata Santa Catarina para 01", () => {
    const result = formatRoomEntityPresentation("order", "01|102942", null);
    expect(result.chipLabel).toBe("Santa Catarina");
  });

  it("falha aberta para outros entity_type", () => {
    expect(formatRoomEntityPresentation("customer", "0001|01", null).chipLabel).toBeNull();
  });
});
