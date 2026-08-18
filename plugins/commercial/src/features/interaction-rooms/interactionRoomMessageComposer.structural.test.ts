import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMessageComposer", () => {
  it("usa FileDropzone/PreviewStrip, upload room_message e suggest no composer", () => {
    const source = readFileSync(
      join(dir, "InteractionRoomMessageComposer.tsx"),
      "utf8",
    );
    expect(source).toMatch(/CommercialFileDropzone/);
    expect(source).toMatch(/CommercialAttachmentPreviewStrip/);
    expect(source).toMatch(/CommercialMentionComposer/);
    expect(source).toMatch(/postInteractionMessage/);
    expect(source).toMatch(/uploadRoomMessageAttachment/);
    expect(source).toMatch(/useInteractionMentionSuggest/);
    expect(source).toMatch(/onMentionQueryChange/);
    expect(source).not.toMatch(/api-delpi/);
    expect(source).not.toMatch(/owner_type:\s*["']task["']/);
  });
});
