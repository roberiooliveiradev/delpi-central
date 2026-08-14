import { describe, expect, it } from "vitest";

import { withPersonAvatarSrc } from "./orgFlowPersonAvatars";

describe("withPersonAvatarSrc", () => {
  it("anexa avatarSrc só em nós de pessoa com foto", () => {
    const nodes = [
      {
        id: "person:u1",
        kind: "person" as const,
        entityId: "u1",
        title: "Ana",
        subtitle: "ana@ex.com",
      },
      {
        id: "group:g1",
        kind: "group" as const,
        entityId: "g1",
        title: "Inside",
      },
      {
        id: "person:u2",
        kind: "person" as const,
        entityId: "u2",
        title: "Bia",
      },
    ];
    const photos = new Map([["u1", "blob:photo-ana"]]);
    const next = withPersonAvatarSrc(nodes, photos);
    expect(next[0]?.avatarSrc).toBe("blob:photo-ana");
    expect(next[1]?.avatarSrc).toBeUndefined();
    expect(next[2]?.avatarSrc).toBeUndefined();
  });
});
