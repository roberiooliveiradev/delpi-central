import { describe, expect, it } from "vitest";

import {
  formatInteractionRoomPinByOtherNotice,
  formatInteractionRoomReactionByOtherNotice,
  interactionRoomComposerNoticeSurface,
  interactionRoomThirdPartyRealtimeNoticeSurface,
  isInteractionRoomOwnActor,
} from "./interactionRoomNoticePolicy";

describe("interactionRoomNoticePolicy", () => {
  it("composer e realtime de terceiros usam floating", () => {
    expect(interactionRoomComposerNoticeSurface()).toBe("floating");
    expect(interactionRoomThirdPartyRealtimeNoticeSurface()).toBe("floating");
  });

  it("ignora actor local", () => {
    expect(isInteractionRoomOwnActor("u1", "u1")).toBe(true);
    expect(isInteractionRoomOwnActor("u2", "u1")).toBe(false);
  });

  it("formata notices de pin e reação", () => {
    expect(formatInteractionRoomPinByOtherNotice("Ana")).toMatch(/Ana/);
    expect(formatInteractionRoomReactionByOtherNotice("Bruno", "👍")).toMatch(/👍/);
  });
});
