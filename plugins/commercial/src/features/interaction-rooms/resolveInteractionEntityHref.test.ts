import { describe, expect, it } from "vitest";

import {
  parseRoomEntityKey,
  resolveInteractionEntityHref,
  resolveRoomEntityHref,
} from "./resolveInteractionEntityHref";

describe("resolveRoomEntityHref", () => {
  it("parseia chave pipe e monta path de conta e pedido", () => {
    expect(parseRoomEntityKey("0001|01")).toEqual(["0001", "01"]);
    expect(parseRoomEntityKey("01")).toBeNull();
    expect(
      resolveRoomEntityHref("/apps/commercial", "customer", "0001|01"),
    ).toContain("/customers/0001/01");
    expect(
      resolveRoomEntityHref("/apps/commercial", "order", "01|102942"),
    ).toContain("/open-orders/01/102942");
    expect(resolveRoomEntityHref("/apps/commercial", "wall", "x|y")).toBeNull();
  });

  it("mantém fail-open no catálogo de menções", () => {
    expect(
      resolveInteractionEntityHref("/apps/commercial", "unknown", {}),
    ).toBeNull();
  });
});
