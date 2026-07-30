import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EditorChrome } from "./EditorChrome";

describe("EditorChrome", () => {
  it("monta head, ribbon e body com densidade compact", () => {
    const { container } = render(
      <EditorChrome
        leading={<button type="button">Voltar</button>}
        tabs={<span>Elementos</span>}
        trail="Título"
        ribbon={<div>Ribbon</div>}
        aria-label="Editor"
      >
        <div>Canvas</div>
      </EditorChrome>,
    );
    const root = container.querySelector(".delpi-ui-editor-chrome");
    expect(root?.getAttribute("data-delpi-ui-density")).toBe("compact");
    expect(screen.getByRole("button", { name: "Voltar" })).toBeTruthy();
    expect(screen.getByText("Elementos")).toBeTruthy();
    expect(screen.getByText("Título")).toBeTruthy();
    expect(screen.getByText("Ribbon")).toBeTruthy();
    expect(screen.getByText("Canvas")).toBeTruthy();
  });
});
