import { describe, expect, it } from "vitest";

import type { InteractionMessageDto } from "../../api/interactionRoomsApi";
import { applyInteractionRoomRealtime } from "./applyInteractionRoomRealtime";

const base: InteractionMessageDto = {
  id: "m1",
  room_id: "r1",
  message_kind: "text",
  body_text: "oi",
  created_at: "2026-08-19T10:00:00Z",
};

describe("applyInteractionRoomRealtime", () => {
  it("append created e ignora duplicata / eco do mesmo clientId", () => {
    const created = applyInteractionRoomRealtime(
      { messages: [], pinnedMessageIds: new Set() },
      {
        type: "room.message.created",
        roomId: "r1",
        messageId: "m1",
        message: base as unknown as Record<string, unknown>,
      },
    );
    expect(created.messages).toHaveLength(1);

    const dup = applyInteractionRoomRealtime(created, {
      type: "room.message.created",
      roomId: "r1",
      messageId: "m1",
      message: { ...base, body_text: "oi" } as unknown as Record<string, unknown>,
    });
    expect(dup.messages).toHaveLength(1);

    const echo = applyInteractionRoomRealtime(
      { messages: [base], pinnedMessageIds: new Set() },
      {
        type: "room.message.created",
        roomId: "r1",
        messageId: "m2",
        actorClientId: "c1",
        message: { ...base, id: "m2" } as unknown as Record<string, unknown>,
      },
      { ignoreActorClientId: "c1" },
    );
    expect(echo.messages).toHaveLength(1);
  });

  it("atualiza texto, marca deleted e pin", () => {
    const updated = applyInteractionRoomRealtime(
      { messages: [base], pinnedMessageIds: new Set() },
      {
        type: "room.message.updated",
        roomId: "r1",
        messageId: "m1",
        message: { ...base, body_text: "edit" } as unknown as Record<string, unknown>,
      },
    );
    expect(updated.messages[0]?.body_text).toBe("edit");

    const deleted = applyInteractionRoomRealtime(updated, {
      type: "room.message.deleted",
      roomId: "r1",
      messageId: "m1",
    });
    expect(deleted.messages[0]?.deleted_at).toBeTruthy();

    const pinned = applyInteractionRoomRealtime(deleted, {
      type: "room.pin",
      roomId: "r1",
      messageId: "m1",
      action: "set",
    });
    expect(pinned.pinnedMessageIds.has("m1")).toBe(true);
    const unpinned = applyInteractionRoomRealtime(pinned, {
      type: "room.pin",
      roomId: "r1",
      messageId: "m1",
      action: "clear",
    });
    expect(unpinned.pinnedMessageIds.has("m1")).toBe(false);
  });

  it("reação set/clear; inbox e mention não mexem na thread", () => {
    const withReaction = applyInteractionRoomRealtime(
      { messages: [base], pinnedMessageIds: new Set() },
      {
        type: "room.reaction",
        roomId: "r1",
        messageId: "m1",
        code: "ok",
        action: "set",
        userId: "u2",
      },
    );
    expect(withReaction.messages[0]?.reactions).toHaveLength(1);
    const cleared = applyInteractionRoomRealtime(withReaction, {
      type: "room.reaction",
      roomId: "r1",
      messageId: "m1",
      code: "ok",
      action: "clear",
      userId: "u2",
    });
    expect(cleared.messages[0]?.reactions).toHaveLength(0);

    const inbox = applyInteractionRoomRealtime(cleared, {
      type: "room.inbox.changed",
      roomId: "r1",
    });
    expect(inbox).toBe(cleared);
  });
});

  it("ignora room.deleted (navegação fica no host)", () => {
    const next = applyInteractionRoomRealtime(
      { messages: [base], pinnedMessageIds: new Set(["m1"]) },
      { type: "room.deleted", roomId: "r1" },
    );
    expect(next.messages).toHaveLength(1);
    expect(next.pinnedMessageIds.has("m1")).toBe(true);
  });
