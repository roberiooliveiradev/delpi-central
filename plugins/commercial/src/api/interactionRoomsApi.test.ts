import { describe, expect, it } from "vitest";

import {
  INTERACTION_ROOMS_API_BASE,
  ROOM_MESSAGE_OWNER_TYPE,
  interactionRoomEntityPreviewPath,
  interactionRoomMentionSuggestPath,
  interactionRoomMemberPath,
  interactionRoomMessagePath,
  interactionRoomMessagesPath,
  interactionRoomPath,
  interactionRoomReactionPath,
  interactionRoomReadPath,
  interactionRoomResolvePath,
  interactionRoomsCollectionPath,
  interactionRoomsUrl,
} from "./interactionRoomsApi";
import { COMMERCIAL_API_BASE } from "./httpClient";

describe("interactionRoomsApi paths", () => {
  it("uses EN interaction-rooms paths under commercial-api", () => {
    expect(INTERACTION_ROOMS_API_BASE).toBe("/interaction-rooms");
    expect(interactionRoomsCollectionPath()).toBe("/interaction-rooms");
    expect(interactionRoomResolvePath()).toBe("/interaction-rooms/resolve");
    expect(interactionRoomMentionSuggestPath()).toBe(
      "/interaction-rooms/mention-suggest",
    );
    expect(interactionRoomEntityPreviewPath()).toBe(
      "/interaction-rooms/entity-preview",
    );
    expect(interactionRoomPath("r1")).toBe("/interaction-rooms/r1");
    expect(interactionRoomMessagesPath("r1")).toBe("/interaction-rooms/r1/messages");
    expect(interactionRoomMessagePath("r1", "m1")).toBe(
      "/interaction-rooms/r1/messages/m1",
    );
    expect(interactionRoomReactionPath("r1", "m1", "thumbsup")).toBe(
      "/interaction-rooms/r1/messages/m1/reactions/thumbsup",
    );
    expect(interactionRoomReadPath("r1")).toBe("/interaction-rooms/r1/read");
    expect(interactionRoomMemberPath("r1", "u1")).toBe(
      "/interaction-rooms/r1/members/u1",
    );
  });

  it("prefixes commercial-api gateway and never api-delpi", () => {
    const url = interactionRoomsUrl(interactionRoomsCollectionPath());
    expect(url).toBe(`${COMMERCIAL_API_BASE}/interaction-rooms`);
    expect(url).toContain("/apps/commercial-api/");
    expect(url).not.toContain("api-delpi");
  });

  it("uses room_message owner type for attachments", () => {
    expect(ROOM_MESSAGE_OWNER_TYPE).toBe("room_message");
  });
});
