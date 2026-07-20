import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DELPI_MODAL_HOST_ATTR } from "../feedback/ModalShell";
import { modalShellBemClasses } from "../feedback/ModalShell";
import { FilePreviewModal } from "./FilePreviewModal";

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

describe("FilePreviewModal host containment", () => {
  afterEach(() => {
    cleanup();
  });

  it("porta o modal no host MFE sem cobrir o viewport inteiro", () => {
    const host = document.createElement("main");
    host.className = "dashboard-transformometro";
    document.body.appendChild(host);

    const mount = document.createElement("div");
    host.appendChild(mount);

    render(
      <FilePreviewModal
        open
        title="Igd Idd Final 1.pdf"
        onClose={vi.fn()}
        previewState={{ status: "ready", kind: "pdf", objectUrl: "blob:test" }}
      />,
      { container: mount },
    );

    const dialog = screen.getByRole("dialog", { name: "Igd Idd Final 1.pdf" });
    expect(host.contains(dialog)).toBe(true);
    expect(host.getAttribute(DELPI_MODAL_HOST_ATTR)).toBe("true");
    expect(dialog.classList.contains("delpi-ui-modal--host-fill")).toBe(true);
    expect(dialog.closest(".delpi-ui-modal-overlay--contained")).toBeTruthy();
    expect(dialog.closest("[data-modal-contained='true']")).toBeTruthy();

    host.remove();
  });

  it("permite overlay fullscreen quando containInHost=false", () => {
    const host = document.createElement("main");
    host.className = "dashboard-transformometro";
    document.body.appendChild(host);
    const mount = document.createElement("div");
    host.appendChild(mount);

    render(
      <FilePreviewModal
        open
        title="Fullscreen.pdf"
        onClose={vi.fn()}
        containInHost={false}
        previewState={{ status: "ready", kind: "pdf", objectUrl: "blob:test" }}
      />,
      { container: mount },
    );

    const dialog = screen.getByRole("dialog", { name: "Fullscreen.pdf" });
    expect(host.contains(dialog)).toBe(false);
    expect(document.body.contains(dialog)).toBe(true);
    expect(dialog.classList.contains("delpi-ui-modal--host-fill")).toBe(false);

    host.remove();
  });
});
