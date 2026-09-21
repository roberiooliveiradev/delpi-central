import { describe, expect, it } from "vitest";

import {
  aggregateReactionBarItems,
  reactionLabelForCode,
} from "./reactionDisplay";

describe("reactionDisplay", () => {
  it("mapeia id do catálogo para glyph", () => {
    expect(reactionLabelForCode("check")).toBe("✅");
    expect(reactionLabelForCode("thumbs_up")).toMatch(/\S/);
  });

  it("mantém código desconhecido", () => {
    expect(reactionLabelForCode("custom-code")).toBe("custom-code");
    expect(reactionLabelForCode("  ")).toBe("");
  });

  it("agrega contagem e reactedByMe com label glyph", () => {
    const items = aggregateReactionBarItems(
      [
        { code: "check", user_id: "u1" },
        { code: "check", user_id: "u2" },
        { code: "fire", user_id: "u1" },
      ],
      "u1",
    );
    expect(items).toEqual([
      { code: "check", label: "✅", count: 2, reactedByMe: true },
      { code: "fire", label: expect.any(String), count: 1, reactedByMe: true },
    ]);
    expect(items.find((item) => item.code === "fire")?.label).not.toBe("fire");
  });
});
