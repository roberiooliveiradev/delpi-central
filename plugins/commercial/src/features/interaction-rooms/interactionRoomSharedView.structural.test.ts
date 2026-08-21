import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomSharedView", () => {
  it("usa listRoomSharedItems e Carregar via attach da sala", () => {
    const source = readFileSync(join(dir, "InteractionRoomSharedView.tsx"), "utf8");
    expect(source).toMatch(/listRoomSharedItems/);
    expect(source).toMatch(/uploadRoomMessageAttachment/);
    expect(source).toMatch(/postInteractionMessage/);
    expect(source).toMatch(/CommercialUnderlineNav/);
    expect(source).not.toMatch(/api-delpi/);
  });
});
