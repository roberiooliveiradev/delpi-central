import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";

import { ModalFrame, modalFrameClassName } from "./ModalFrame";
import { ModalShell, modalShellBemClasses } from "./ModalShell";

describe("ModalFrame", () => {
  it("aplica classe canônica do chrome", () => {
    expect(modalFrameClassName("extra")).toBe("delpi-ui-modal-frame extra");
    render(
      <ModalFrame data-testid="frame">
        <p>conteúdo</p>
      </ModalFrame>,
    );
    expect(screen.getByTestId("frame").className).toContain("delpi-ui-modal-frame");
  });
});

describe("ModalShell + ModalFrame chrome", () => {
  it("sempre emite delpi-ui-modal-frame no card", () => {
    render(
      <ModalShell open title="Biblioteca" onClose={vi.fn()} classNames={modalShellBemClasses("td")}>
        <p>corpo</p>
      </ModalShell>,
    );
    const dialog = screen.getByRole("dialog", { name: "Biblioteca" });
    expect(dialog.className).toContain("delpi-ui-modal-frame");
    expect(dialog.className).toContain("delpi-ui-modal");
  });
});

describe("modal-frame.css contract", () => {
  const css = readFileSync(resolve(__dirname, "../../styles/modal-frame.css"), "utf8");
  const stylesEntry = readFileSync(resolve(__dirname, "../../styles.css"), "utf8");

  it("está no kit e define tokens do confirm", () => {
    expect(stylesEntry).toContain('import "./styles/modal-frame.css"');
    expect(css).toContain("--delpi-ui-modal-radius: 20px");
    expect(css).toContain("--delpi-ui-modal-shadow");
    expect(css).toContain(".delpi-ui-modal-frame");
  });
});
