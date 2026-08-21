import { describe, expect, it } from "vitest";

import {
  buildInteractionRoomSubscribePayload,
  buildInteractionRoomUnsubscribePayload,
  interactionRoomEventTouchesRoom,
  isInteractionRoomEventType,
  isInteractionRoomFanoutType,
  isInteractionRoomUserType,
} from "./interactionRoomRealtime";
import { parseCommercialRealtimeEvent } from "./realtime";

describe("interactionRoomRealtime protocol", () => {
  it("monta subscribe/unsubscribe com roomId EN", () => {
    expect(JSON.parse(buildInteractionRoomSubscribePayload("  abc-1  "))).toEqual({
      type: "subscribe",
      roomId: "abc-1",
    });
    expect(JSON.parse(buildInteractionRoomUnsubscribePayload("abc-1"))).toEqual({
      type: "unsubscribe",
      roomId: "abc-1",
    });
  });

  it("classifica tipos room.* de fan-out e user:", () => {
    expect(isInteractionRoomFanoutType("room.message.created")).toBe(true);
    expect(isInteractionRoomFanoutType("room.deleted")).toBe(true);
    expect(isInteractionRoomFanoutType("room.reaction")).toBe(true);
    expect(isInteractionRoomFanoutType("room.mention")).toBe(false);
    expect(isInteractionRoomUserType("room.mention")).toBe(true);
    expect(isInteractionRoomUserType("room.attachment")).toBe(true);
    expect(isInteractionRoomFanoutType("room.pin")).toBe(true);
    expect(isInteractionRoomFanoutType("room.inbox.changed")).toBe(true);
    expect(isInteractionRoomEventType("room.inbox.changed")).toBe(true);
    expect(isInteractionRoomEventType("worklist.changed")).toBe(false);
  });

  it("filtra evento pela sala aberta", () => {
    expect(
      interactionRoomEventTouchesRoom({ roomId: "r1" }, "r1"),
    ).toBe(true);
    expect(
      interactionRoomEventTouchesRoom({ roomId: "r1" }, "r2"),
    ).toBe(false);
  });

  it("parseCommercialRealtimeEvent aceita room.message.created", () => {
    const raw = JSON.stringify({
      type: "room.message.created",
      roomId: "r1",
      messageId: "m1",
      message: { id: "m1", body_text: "oi" },
    });
    const event = parseCommercialRealtimeEvent(raw);
    expect(event?.type).toBe("room.message.created");
    if (event && "roomId" in event) {
      expect(event.roomId).toBe("r1");
    }
  });
});
