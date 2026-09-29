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
