import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(dir, relativePath), "utf8");
}

/**
 * Regression: dropped/picked non-image files (PDF, DOCX, …) used to vanish —
 * they were queued in pendingFilesRef but never rendered. The composer must
 * stage them as removable chips and upload them on submit.
 */
describe("Helpdesk pending attachments structural", () => {
  it("rich text field renders a manage strip for staged attachments", () => {
    const ui = read("../ui/helpdeskUi.tsx");
    expect(ui).toContain("HelpdeskPendingAttachmentItem");
    expect(ui).toContain("pendingAttachments");
    expect(ui).toContain("onPendingAttachmentOpen");
    expect(ui).toContain("onPendingAttachmentRemove");
    expect(ui).toContain('mode="manage"');
    expect(ui).toContain("HelpdeskAttachmentPreviewStrip");
  });

  it("create composer stages non-image files and uploads them on submit", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).toContain("function isInlineImageFile");
    expect(page).toContain("setPendingAttachments");
    expect(page).toContain("onPendingAttachmentRemove={removePendingAttachment}");
    expect(page).toContain("onPendingAttachmentOpen={(id) => setPendingPreviewId(id)}");
    // submit drains the staged map — pending ids include non-image keys
    expect(page).toContain("pendingFilesRef.current.keys()");
  });

  it("reply composer defers non-image upload to submit (removable before send)", () => {
    const page = read("HelpdeskPage.tsx");
    const uploadHandler = page.indexOf("onUploadFiles={async (files) => {");
    expect(uploadHandler).toBeGreaterThan(-1);
    const segment = page.slice(uploadHandler, uploadHandler + 4000);
    expect(segment).toContain("staged.push");
    // non-images must NOT upload immediately inside onUploadFiles
    const nonImageBranch = segment.indexOf("if (!isInlineImageFile(file))");
    expect(nonImageBranch).toBeGreaterThan(-1);
    const branchBody = segment.slice(nonImageBranch, segment.indexOf("continue;", nonImageBranch));
    expect(branchBody).not.toContain("uploadTicketAttachment(");
  });

  it("P0: attach picker carries explicit attachment intent — never MIME-inferred", () => {
    const page = read("HelpdeskPage.tsx");
    const ui = read("../ui/helpdeskUi.tsx");
    // The picker contract carries an explicit intent — accept filter is not
    // a semantic. Both create buttons and the reply attach button declare it.
    expect(ui).toContain("HelpdeskUploadIntent");
    expect(ui).toContain("pickerIntentRef");
    expect(ui).toContain("onAttachFiles");
    expect(page).toContain('intent: "attachment"');
    expect(page).toContain('intent: "inline"');
    // Attachment-intent files stage through a dedicated handler — images
    // included — and never pass through the editor ingest path.
    expect(page).toContain("const stagePendingAttachments = (files: File[])");
    expect(page).toContain("onAttachFiles={stagePendingAttachments}");
    expect(page).toContain("const stageReplyAttachments = (files: File[])");
    expect(page).toContain("onAttachFiles={stageReplyAttachments}");
    // Per-id intent persists with the draft row (survives F5).
    expect(page).toContain("pendingKindsRef");
    const draft = read("../presentation/helpdeskDraftPendingFiles.ts");
    expect(draft).toContain('kind?: HelpdeskDraftPendingKind');
    expect(draft).toContain("resolveHelpdeskDraftPendingKind");
    // A removed inline image must not upload silently — the onChange diff
    // reconcile drops the orphan pending row before submit.
    const inline = read("../presentation/inlineUpload.ts");
    expect(inline).toContain("listRemovedPendingInlineIds");
    expect(page).toContain("reconcileCreatePendingRemoval(description, persisted)");
    expect(page).toContain("reconcileReplyPendingRemoval(content, persisted)");
  });

  it("P0: restored attachment images keep their remove chrome (editor hydrates)", () => {
    const kit = read("../../../plugin-ui/src/components/rich-text/RichTextEditor.tsx");
    const inline = read("../../../plugin-ui/src/components/rich-text/richTextInlineImage.ts");
    // Drafts strip the __inline-image wrapper + × button — the editor must
    // restore that chrome on attachment images when the html is re-injected,
    // otherwise a restored image has no removal path (the reported F5 bug).
    expect(inline).toContain("hydrateRichTextInlineImageChrome");
    expect(kit).toContain("hydrateRichTextInlineImageChrome(editorRef.current)");
  });

  it("degraded upload authorship surfaces a notice — never silent full success", () => {
    const page = read("HelpdeskPage.tsx");
    // Every upload call site must check author_verified before continuing
    const checks = page.split("attachmentAuthorDegraded(uploaded)").length - 1;
    expect(checks).toBeGreaterThanOrEqual(4);
    // create flow stages the notice across the navigation boundary…
    expect(page).toContain("stageAttachmentAuthorNotice()");
    // …and the ticket detail consumes + renders it as a banner
    expect(page).toContain("consumeAttachmentAuthorNotice()");
    expect(page).toContain("noticeText");
    expect(page).toContain("{noticeText ? <HelpdeskStateBanner>{noticeText}</HelpdeskStateBanner> : null}");
    // the notice must describe partial outcome, not claim success
    const notice = read("../presentation/attachmentAuthorNotice.ts");
    expect(notice).toContain("autoria do envio não pôde ser confirmada");
    expect(notice).toContain("documento está preservado");
  });

  it("fill layout cannot overflow the card — card shrinks and body scrolls", () => {
    const css = read("../index.css");
    // trailing utility siblings (FilePreviewModal hidden anchor) take :last-child,
    // so the fill card needs an explicit shrink override
    expect(css).toContain("helpdesk-page-stack > .delpi-ui-section-card--fill");
    expect(css).toMatch(/section-card--fill\s*{[^}]*flex-shrink:\s*1/);
    // drop wrapper must be a flex column so the editor yields space to the strip
    expect(css).toMatch(/rich-text-field--fill\s*>\s*\.helpdesk-conversation-drop[^{]*{[^}]*flex-direction:\s*column/);
    const uiCss = read("../../../plugin-ui/src/styles/section-card.css");
    // height:100% on a flex child double-counts siblings — flex must govern
    const fillRule = uiCss.match(/\.delpi-ui-section-card--fill\s*{([^}]*)}/);
    expect(fillRule).not.toBeNull();
    expect(fillRule![1]).not.toContain("height: 100%");
    expect(fillRule![1]).not.toContain("height:100%");
    // body must scroll, not clip, when content exceeds the card
    expect(uiCss).toMatch(/section-card__body\s*{[^}]*overflow-y:\s*auto/);
    const richCss = read("../../../plugin-ui/src/styles/rich-text-editor.css");
    const richFill = richCss.match(/\.delpi-ui-rich-text--fill\s*{([^}]*)}/);
    expect(richFill).not.toBeNull();
    expect(richFill![1]).not.toContain("height: 100%");
    expect(richFill![1]).not.toContain("height:100%");
  });
});
