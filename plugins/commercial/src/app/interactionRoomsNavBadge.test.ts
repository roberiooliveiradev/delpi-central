import { describe, expect, it } from "vitest";

import { sumInboxUnreadCount } from "./interactionRoomsNavBadge";

describe("sumInboxUnreadCount", () => {
  it("soma não lidas e ignora valores inválidos", () => {
    expect(sumInboxUnreadCount(null)).toBe(0);
    expect(
      sumInboxUnreadCount([
        { unread_count: 2 },
        { unread_count: 0 },
        { unread_count: 3.9 },
        { unread_count: -1 },
        {},
      ]),
    ).toBe(5);
  });
});
