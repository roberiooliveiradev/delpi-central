import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomSharedView", () => {
  it("lista shared-items em modo consulta sem Carregar", () => {
    const source = readFileSync(join(dir, "InteractionRoomSharedView.tsx"), "utf8");
    expect(source).toMatch(/listRoomSharedItems/);
    expect(source).toMatch(/hideLabel/);
    expect(source).toMatch(/CommercialAvatar/);
    expect(source).toMatch(/CommercialUnderlineNav/);
    expect(source).not.toMatch(/uploadRoomMessageAttachment/);
    expect(source).not.toMatch(/postInteractionMessage/);
    expect(source).not.toMatch(/sharedUploadLabel/);
    expect(source).not.toMatch(/api-delpi/);
  });
});
