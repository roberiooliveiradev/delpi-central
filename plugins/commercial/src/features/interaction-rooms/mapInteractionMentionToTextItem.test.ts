import { describe, expect, it } from "vitest";

import { mapInteractionMentionToTextItem } from "./mapInteractionMentionToTextItem";

describe("mapInteractionMentionToTextItem", () => {
  it("maps user mention with href, title and avatar fields", () => {
    const photos = new Map([["u1", "blob:photo-1"]]);
    const item = mapInteractionMentionToTextItem(
      {
        mention_kind: "user",
        label: "@Ana Silva",
        ref: { user_id: "u1" },
      },
      { basePath: "/apps/commercial", photoByUserId: photos },
    );
    expect(item.kind).toBe("user");
    expect(item.href).toContain("/users/u1");
    expect(item.title).toMatch(/Ana Silva/);
    expect(item.avatarName).toBe("Ana Silva");
    expect(item.avatarSrc).toBe("blob:photo-1");
  });

  it("leaves non-user mentions without avatar chrome", () => {
    const item = mapInteractionMentionToTextItem(
      {
        mention_kind: "order",
        label: "102942",
        ref: { order: "102942", branch: "01" },
      },
      { basePath: "/apps/commercial" },
    );
    expect(item.kind).toBe("order");
    expect(item.avatarName).toBeUndefined();
    expect(item.href).toBeUndefined();
  });
});
