import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMessageAttachments", () => {
  it("lista anexos room_message e abre FilePreviewModal via strip", () => {
    const source = readFileSync(
      join(dir, "InteractionRoomMessageAttachments.tsx"),
      "utf8",
    );
    expect(source).toMatch(/listRoomMessageAttachments/);
    expect(source).toMatch(/downloadRoomMessageAttachmentBlob/);
    expect(source).toMatch(/CommercialAttachmentPreviewStrip/);
    expect(source).toMatch(/TaskAttachmentPreviewModal/);
    expect(source).toMatch(/FilePreviewModal|TaskAttachmentPreviewModal/);
    expect(source).toMatch(/mode="preview"/);
    expect(source).toMatch(/reloadToken/);
    expect(source).not.toMatch(/api-delpi/);
    expect(source).not.toMatch(/window\.confirm/);
  });
});
