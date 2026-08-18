import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMessageComposer", () => {
  it("usa FileDropzone/PreviewStrip e upload room_message após POST", () => {
    const source = readFileSync(
      join(dir, "InteractionRoomMessageComposer.tsx"),
      "utf8",
    );
    expect(source).toMatch(/CommercialFileDropzone/);
    expect(source).toMatch(/CommercialAttachmentPreviewStrip/);
    expect(source).toMatch(/CommercialMentionComposer/);
    expect(source).toMatch(/postInteractionMessage/);
    expect(source).toMatch(/uploadRoomMessageAttachment/);
    expect(source).toMatch(/ROOM_MESSAGE_OWNER_TYPE|uploadRoomMessageAttachment/);
    expect(source).not.toMatch(/api-delpi/);
    expect(source).not.toMatch(/owner_type:\s*["']task["']/);
  });
});
