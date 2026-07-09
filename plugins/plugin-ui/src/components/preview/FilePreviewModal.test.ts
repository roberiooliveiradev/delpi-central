import { describe, expect, it } from "vitest";

import { modalShellBemClasses } from "../feedback/ModalShell";

describe("FilePreviewModal class names", () => {
  it("usa prefixo delpi-ui-file-preview para casar com file-preview.css", () => {
    const classNames = modalShellBemClasses("delpi-ui-file-preview");

    expect(classNames.overlay).toBe("delpi-ui-file-preview-modal-overlay");
    expect(classNames.dialog).toBe("delpi-ui-file-preview-modal");
    expect(classNames.header).toBe("delpi-ui-file-preview-modal__header");
    expect(classNames.body).toBe("delpi-ui-file-preview-modal__body");
  });
});
