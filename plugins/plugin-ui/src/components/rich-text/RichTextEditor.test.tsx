import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RichTextEditor } from "./RichTextEditor";
import { RICH_TEXT_LABELS } from "./richTextLabels";

describe("RichTextEditor", () => {
  it("renderiza ribbon Fonte e Parágrafo no modo edit", () => {
    render(<RichTextEditor value="<p>Teste</p>" onChange={() => undefined} />);
    expect(screen.getByRole("toolbar", { name: RICH_TEXT_LABELS.toolbar })).toBeTruthy();
    expect(screen.getByText(RICH_TEXT_LABELS.fontSection)).toBeTruthy();
    expect(screen.getByText(RICH_TEXT_LABELS.paragraphSection)).toBeTruthy();
    expect(screen.getByRole("textbox", { name: "Editor de texto" })).toBeTruthy();
  });

  it("renderiza preview sem toolbar", () => {
    const { container } = render(
      <RichTextEditor value="<p>Preview</p>" onChange={() => undefined} mode="preview" />,
    );
    expect(container.querySelector(".delpi-ui-rich-text-ribbon")).toBeNull();
    expect(container.querySelector(".delpi-ui-rich-text--preview")?.textContent).toContain("Preview");
  });
});
