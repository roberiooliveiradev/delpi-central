import { describe, expect, it } from "vitest";

import { interactionRoomSharedItemsPath } from "../../api/interactionRoomsApi";

describe("interactionRoomSharedItems client path", () => {
  it("monta path EN shared-items", () => {
    expect(interactionRoomSharedItemsPath("abc-1")).toBe(
      "/interaction-rooms/abc-1/shared-items",
    );
    expect(interactionRoomSharedItemsPath("abc-1")).not.toMatch(/compartilhado/);
  });
});
