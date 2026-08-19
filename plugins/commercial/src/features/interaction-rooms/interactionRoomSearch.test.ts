import { describe, expect, it } from "vitest";

import {
  buildInteractionRoomSearch,
  parseInteractionRoomSearch,
} from "./interactionRoomSearch";

describe("interactionRoomSearch", () => {
  it("parses filter and q without dropping values", () => {
    expect(parseInteractionRoomSearch("?filter=unread&q=pedido")).toEqual({
      filter: "unread",
      q: "pedido",
    });
  });

  it("omits default all filter from the query string", () => {
    expect(buildInteractionRoomSearch({ filter: "all", q: "" })).toBe("");
    expect(buildInteractionRoomSearch({ filter: "wall", q: "acme" })).toBe(
      "?filter=wall&q=acme",
    );
  });
});
