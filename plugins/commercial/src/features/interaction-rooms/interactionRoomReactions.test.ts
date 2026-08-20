import { describe, expect, it } from "vitest";

import {
  aggregateMessageReactions,
  applyLocalReactionToggle,
  reactionLabelForCode,
} from "./interactionRoomReactions";

describe("interactionRoomReactions", () => {
  it("agrega contagem e reactedByMe", () => {
    const items = aggregateMessageReactions(
      [
        { message_id: "m1", user_id: "u1", code: "thumbsup" },
        { message_id: "m1", user_id: "u2", code: "thumbsup" },
        { message_id: "m1", user_id: "u1", code: "heart" },
      ],
      "u1",
    );
    expect(items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: "thumbsup",
          count: 2,
          reactedByMe: true,
        }),
        expect.objectContaining({
          code: "heart",
          count: 1,
          reactedByMe: true,
        }),
      ]),
    );
  });

  it("aplica toggle local set/clear", () => {
    const base = [{ message_id: "m1", user_id: "u1", code: "thumbsup" }];
    const cleared = applyLocalReactionToggle(base, {
      messageId: "m1",
      userId: "u1",
      code: "thumbsup",
      nextActive: false,
    });
    expect(cleared).toEqual([]);
    const set = applyLocalReactionToggle(cleared, {
      messageId: "m1",
      userId: "u1",
      code: "heart",
      nextActive: true,
    });
    expect(set).toEqual([
      { message_id: "m1", user_id: "u1", code: "heart" },
    ]);
  });

  it("label cai no code quando fora do catálogo", () => {
    expect(reactionLabelForCode("custom-code")).toBe("custom-code");
  });
});
