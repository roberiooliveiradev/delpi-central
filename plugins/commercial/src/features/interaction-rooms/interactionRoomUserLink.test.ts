import { describe, expect, it } from "vitest";

import { interactionRoomParticipantAvatar, interactionRoomUserLink } from "./interactionRoomUserLink";

describe("interactionRoomUserLink", () => {
  it("monta href de perfil e title Abrir perfil", () => {
    const link = interactionRoomUserLink("u-1", "Ana Silva", "/apps/commercial");
    expect(link?.href).toContain("/users/u-1");
    expect(link?.title).toBe("Abrir perfil de Ana Silva");
    const participant = interactionRoomParticipantAvatar(
      "u-1",
      "Ana Silva",
      "/apps/commercial",
    );
    expect(participant.href).toContain("/users/u-1");
    expect(participant.title).toBe("Abrir perfil de Ana Silva");
  });

  it("retorna null sem userId", () => {
    expect(interactionRoomUserLink("", "Ana", "/apps/commercial")).toBeNull();
    expect(interactionRoomUserLink(null, "Ana", "/apps/commercial")).toBeNull();
  });
});
