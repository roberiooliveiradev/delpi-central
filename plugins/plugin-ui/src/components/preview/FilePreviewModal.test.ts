import { describe, expect, it } from "vitest";

import { modalShellBemClasses } from "../feedback/ModalShell";

describe("FilePreviewModal class names", () => {
  it("usa prefixo delpi-ui-file-preview para casar com file-preview.css", () => {
    const classNames = modalShellBemClasses("delpi-ui-file-preview");

    expect(classNames.overlay).toContain("delpi-ui-file-preview-modal-overlay");
    expect(classNames.overlay).toContain("delpi-ui-modal-overlay");
    expect(classNames.dialog).toContain("delpi-ui-file-preview-modal");
    expect(classNames.dialog).toContain("delpi-ui-modal");
    expect(classNames.header).toContain("delpi-ui-file-preview-modal__header");
    expect(classNames.body).toContain("delpi-ui-file-preview-modal__body");
  });
});
