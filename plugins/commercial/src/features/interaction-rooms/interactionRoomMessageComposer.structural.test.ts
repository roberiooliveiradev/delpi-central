import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMessageComposer", () => {
  it("usa clip/onFilesSelected + pendingAttachments no kit, sem dashed permanente", () => {
    const source = readFileSync(
      join(dir, "InteractionRoomMessageComposer.tsx"),
      "utf8",
    );
    expect(source).not.toMatch(/CommercialFileDropzone/);
    expect(source).not.toMatch(/CommercialAttachmentPreviewStrip/);
    expect(source).not.toMatch(/\bfooter=/);
    expect(source).toMatch(/pendingAttachments=/);
    expect(source).toMatch(/onRemovePendingAttachment=/);
    expect(source).toMatch(/CommercialMentionComposer/);
    expect(source).toMatch(/onFilesSelected=/);
    expect(source).toMatch(/onInlineImagesInserted=/);
    expect(source).toMatch(/rewriteInlinePendingInMarkdown/);
    expect(source).toMatch(/uploadInlineAndRewrite/);
    expect(source).toMatch(/bodyInlineImageRewriteFailed/);
    expect(source).toMatch(/listInlinePendingIdsFromMarkdown\(rewritten\)/);
    expect(source).not.toMatch(/hasAttachments=/);
    expect(source).not.toMatch(/body_html/);
    expect(source).toMatch(/body_text:/);
    expect(source).toMatch(/postInteractionMessage/);
    expect(source).toMatch(/uploadRoomMessageAttachment/);
    expect(source).toMatch(/useInteractionMentionSuggest/);
    expect(source).toMatch(/onMentionQueryChange/);
    expect(source).toMatch(/formatToggleAriaLabel:/);
    expect(source).toMatch(/formatAlignLeftAriaLabel:/);
    expect(source).toMatch(/formatAlignCenterAriaLabel:/);
    expect(source).toMatch(/formatAlignRightAriaLabel:/);
    expect(source).toMatch(/formatAlignJustifyAriaLabel:/);
    expect(source).toMatch(/formatUndoAriaLabel:/);
    expect(source).toMatch(/formatRedoAriaLabel:/);
    expect(source).toMatch(/resolveAttachmentImageSrc/);
    expect(source).toMatch(/onInlineAttachmentRemoved/);
    expect(source).toMatch(/listInlineAttachmentIdsFromMarkdown/);
    expect(source).toMatch(/inlineThumbUrls/);
    expect(source).toMatch(/gatePendingAttachments/);
    expect(source).toMatch(/interactionMessageLooksLikeRawHtml/);
    expect(source).toMatch(/bodyHtmlRejected/);
    expect(source).toMatch(/readComposerDraftText/);
    expect(source).toMatch(/writeComposerDraftFiles/);
    expect(source).toMatch(/clearComposerDraft/);
    expect(source).toMatch(/updateInteractionMessage/);
    expect(source).toMatch(/mode === "edit"/);
    expect(source).toMatch(/listRoomMessageAttachments/);
    expect(source).toMatch(/deleteRoomMessageAttachment/);
    expect(source).toMatch(/editBanner/);
    expect(source).toMatch(/clearComposerDraft/);
    expect(source).toMatch(/replyToMessageId|parent_id/);
    expect(source).toMatch(/replyBanner/);
    expect(source).toMatch(/onMessageAttachmentsSettled/);
    expect(source).toMatch(/seedMentions|initialMentions/);
    expect(source).toMatch(/composerSaveEditAriaLabel/);
    expect(source).toMatch(/showAttach/);
    expect(source).not.toMatch(/showAttach=\{!isEdit\}/);
    expect(source).not.toMatch(/<RichTextToolbar|<RichTextEditor/);
    expect(source).not.toMatch(/from ["'][^"']*RichTextToolbar["']/);
    expect(source).not.toMatch(/from ["'][^"']*RichTextEditor["']/);
    expect(source).not.toMatch(/api-delpi/);
    expect(source).not.toMatch(/owner_type:\s*["']task["']/);
  });
});
