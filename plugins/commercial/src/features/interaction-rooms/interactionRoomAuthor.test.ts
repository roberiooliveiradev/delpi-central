import { describe, expect, it } from "vitest";

import { isOwnInteractionAuthor } from "./interactionRoomAuthor";

describe("isOwnInteractionAuthor", () => {
  it("marca só quando os ids coincidem", () => {
    expect(isOwnInteractionAuthor("u1", "u1")).toBe(true);
    expect(isOwnInteractionAuthor("u1", "u2")).toBe(false);
    expect(isOwnInteractionAuthor("u1", null)).toBe(false);
    expect(isOwnInteractionAuthor(null, "u1")).toBe(false);
    expect(isOwnInteractionAuthor(" u1 ", "u1")).toBe(true);
  });
});
