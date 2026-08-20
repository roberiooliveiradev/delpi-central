import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMessageComposer", () => {
  it("usa clip/onFilesSelected + PreviewStrip, sem dashed permanente", () => {
    const source = readFileSync(
      join(dir, "InteractionRoomMessageComposer.tsx"),
      "utf8",
    );
    expect(source).not.toMatch(/CommercialFileDropzone/);
    expect(source).toMatch(/CommercialAttachmentPreviewStrip/);
    expect(source).toMatch(/CommercialMentionComposer/);
    expect(source).toMatch(/onFilesSelected=/);
    expect(source).toMatch(/hasAttachments=/);
    expect(source).not.toMatch(/body_html/);
    expect(source).toMatch(/body_text:/);
    expect(source).toMatch(/postInteractionMessage/);
    expect(source).toMatch(/uploadRoomMessageAttachment/);
    expect(source).toMatch(/useInteractionMentionSuggest/);
    expect(source).toMatch(/onMentionQueryChange/);
    expect(source).toMatch(/formatToggleAriaLabel:/);
    expect(source).toMatch(/formatUndoAriaLabel:/);
    expect(source).toMatch(/formatRedoAriaLabel:/);
    expect(source).toMatch(/gatePendingAttachments/);
    expect(source).toMatch(/interactionMessageLooksLikeRawHtml/);
    expect(source).toMatch(/bodyHtmlRejected/);
    expect(source).toMatch(/readComposerDraftText/);
    expect(source).toMatch(/writeComposerDraftFiles/);
    expect(source).toMatch(/clearComposerDraft/);
    expect(source).not.toMatch(/<RichTextToolbar|<RichTextEditor/);
    expect(source).not.toMatch(/from ["'][^"']*RichTextToolbar["']/);
    expect(source).not.toMatch(/from ["'][^"']*RichTextEditor["']/);
    expect(source).not.toMatch(/api-delpi/);
    expect(source).not.toMatch(/owner_type:\s*["']task["']/);
  });
});
