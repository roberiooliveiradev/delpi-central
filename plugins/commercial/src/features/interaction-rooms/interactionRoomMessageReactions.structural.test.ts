import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMessageReactions", () => {
  it("usa ReactionBar + PUT/DELETE reaction sem window.confirm", () => {
    const source = readFileSync(
      join(dir, "InteractionRoomMessageReactions.tsx"),
      "utf8",
    );
    expect(source).toMatch(/CommercialReactionBar/);
    expect(source).toMatch(/emojiAdd=/);
    expect(source).toMatch(/setInteractionMessageReaction/);
    expect(source).toMatch(/clearInteractionMessageReaction/);
    expect(source).not.toMatch(/window\.confirm/);
    expect(source).not.toMatch(/api-delpi/);
  });
});
